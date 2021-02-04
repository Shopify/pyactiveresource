# Copyright 2008 Google Inc. All Rights Reserved.

"""Utilities for pyActiveResource."""

__author__ = 'Mark Roach (mrroach@google.com)'

import base64
import calendar
import decimal
import re
import time
import datetime
import six
from six.moves import urllib
from pyactiveresource import element_containers
try:
    import yaml
except ImportError:
    yaml = None

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        json = None

try:
    from dateutil.parser import parse as date_parse
except ImportError:
    try:
        from xml.utils import iso8601
        def date_parse(time_string):
            """Return a datetime object for the given ISO8601 string.

            Args:
                time_string: An ISO8601 timestamp.
            Returns:
                A datetime.datetime object.
            """
            return datetime.datetime.utcfromtimestamp(
                    iso8601.parse(time_string))
    except ImportError:
        date_parse = None

try:
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        from xml.etree import ElementTree as ET

XML_HEADER = b'<?xml version="1.0" encoding="UTF-8"?>\n'

# Patterns blatently stolen from Rails' Inflector
PLURALIZE_PATTERNS = [
    (r'(quiz)$', r'\1zes'),
    (r'^(ox)$', r'\1en'),
    (r'([m|l])ouse$', r'\1ice'),
    (r'(matr|vert|ind)(?:ix|ex)$', r'\1ices'),
    (r'(x|ch|ss|sh)$', r'\1es'),
    (r'([^aeiouy]|qu)y$', r'\1ies'),
    (r'(hive)$', r'1s'),
    (r'(?:([^f])fe|([lr])f)$', r'\1\2ves'),
    (r'sis$', r'ses'),
    (r'([ti])um$', r'\1a'),
    (r'(buffal|tomat)o$', r'\1oes'),
    (r'(bu)s$', r'\1ses'),
    (r'(alias|status)$', r'\1es'),
    (r'(octop|vir)us$', r'\1i'),
    (r'(ax|test)is$', r'\1es'),
    (r's$', 's'),
    (r'$', 's')
]

SINGULARIZE_PATTERNS = [
    (r'(quiz)zes$', r'\1'),
    (r'(matr)ices$', r'\1ix'),
    (r'(vert|ind)ices$', r'\1ex'),
    (r'^(ox)en', r'\1'),
    (r'(alias|status)es$', r'\1'),
    (r'(octop|vir)i$', r'\1us'),
    (r'(cris|ax|test)es$', r'\1is'),
    (r'(shoe)s$', r'\1'),
    (r'(o)es$', r'\1'),
    (r'(bus)es$', r'\1'),
    (r'([m|l])ice$', r'\1ouse'),
    (r'(x|ch|ss|sh)es$', r'\1'),
    (r'(m)ovies$', r'\1ovie'),
    (r'(s)eries$', r'\1eries'),
    (r'([^aeiouy]|qu)ies$', r'\1y'),
    (r'([lr])ves$', r'\1f'),
    (r'(tive)s$', r'\1'),
    (r'(hive)s$', r'\1'),
    (r'([^f])ves$', r'\1fe'),
    (r'(^analy)ses$', r'\1sis'),
    (r'((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$',
     r'\1\2sis'),
    (r'([ti])a$', r'\1um'),
    (r'(n)ews$', r'\1ews'),
    (r's$', r'')
]

IRREGULAR = [
    ('person', 'people'),
    ('man', 'men'),
    ('child', 'children'),
    ('sex', 'sexes'),
    ('move', 'moves'),
    #('cow', 'kine') WTF?
]

UNCOUNTABLES = ['equipment', 'information', 'rice', 'money', 'species',
                'series', 'fish', 'sheep']

# An array of type-specific serializer methods which will be passed the value
# and should return the element type and modified value.
SERIALIZERS = [
    {'type': bool,
     'method': lambda value: ('boolean', six.text_type(value).lower())},
    {'type': six.integer_types,
     'method': lambda value: ('integer', six.text_type(value))}]
if six.PY2:
    SERIALIZERS.append({
        'type': str,
        'method': lambda value: (None, unicode(value, 'utf-8'))})
else:
    SERIALIZERS.append({
        'type': bytes,
        'method': lambda value: ('base64Binary', base64.b64encode(value).decode('ascii'))})

DEFAULT_SERIALIZER = {
    'type': object,
    'method': lambda value: (None, six.text_type(value))}


class Error(Exception):
    """Base exception class for this module."""


class FileObject(object):
    """Represent a 'file' xml entity."""

    def __init__(self, data, name='untitled',
                 content_type='application/octet-stream'):
        self.data = data
        self.name = name
        self.content_type = content_type


def pluralize(singular):
    """Convert singular word to its plural form.

    Args:
        singular: A word in its singular form.

    Returns:
        The word in its plural form.
    """
    if singular in UNCOUNTABLES:
        return singular
    for i in IRREGULAR:
        if i[0] == singular:
            return i[1]
    for i in PLURALIZE_PATTERNS:
        if re.search(i[0], singular):
            return re.sub(i[0], i[1], singular)

def singularize(plural):
    """Convert plural word to its singular form.

    Args:
        plural: A word in its plural form.
    Returns:
        The word in its singular form.
    """
    if plural in UNCOUNTABLES:
        return plural
    for i in IRREGULAR:
        if i[1] == plural:
            return i[0]
    for i in SINGULARIZE_PATTERNS:
        if re.search(i[0], plural):
            return re.sub(i[0], i[1], plural)
    return plural


def camelize(word):
    """Convert a word from lower_with_underscores to CamelCase.

    Args:
        word: The string to convert.
    Returns:
        The modified string.
    """
    return ''.join(w[0].upper() + w[1:]
                   for w in re.sub('[^A-Z^a-z^0-9^:]+', ' ', word).strip().split(' '))


def underscore(word):
    """Convert a word from CamelCase to lower_with_underscores.

    Args:
        word: The string to convert.
    Returns:
        The modified string.
    """
    return re.sub(r'\B((?<=[a-z])[A-Z]|[A-Z](?=[a-z]))',
                  r'_\1', word).lower()


def to_query(query_params):
    """Convert a dictionary to url query parameters.

    Args:
        query_params: A dictionary of arguments.
    Returns:
        A string of query parameters.
    """
    def annotate_params(params):
        annotated = {}
        for key, value in six.iteritems(params):
            if isinstance(value, list):
                key = '%s[]' % key
            elif isinstance(value, dict):
                dict_options = {}
                for dk, dv in six.iteritems(value):
                    dict_options['%s[%s]' % (key, dk)] = dv
                annotated.update(annotate_params(dict_options))
                continue
            elif isinstance(value, six.text_type):
                value = value.encode('utf-8')
            annotated[key] = value
        return annotated
    annotated = annotate_params(query_params)
    return urllib.parse.urlencode(annotated, True)


def xml_pretty_format(element, level=0):
    """Add PrettyPrint formatting to an ElementTree element.

    Args:
        element: An ElementTree element which is modified in-place.
    Returns:
        None
    """
    indent = '\n%s' % ('  ' * level)
    if len(element):
        if not element.text or not element.text.strip():
            element.text = indent + '  '
        for i, child in enumerate(element):
            xml_pretty_format(child, level + 1)
            if not child.tail or not child.tail.strip():
                if i + 1 < len(element):
                    child.tail = indent + "  "
                else:
                    child.tail = indent
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indent


def serialize(value, element):
    """Write a serialized value to an xml element.

    Args:
        value: The value to serialize.
        element: An xml element to write to.
    Returns:
        None
    """
    if value is None:
      element.set('nil', 'true')
      return

    for serializer in SERIALIZERS + [DEFAULT_SERIALIZER]:
        if isinstance(value, serializer['type']):
            element_type, element.text = serializer['method'](value)
            if element_type:
                element.set('type', element_type)
            break


def to_json(obj, root='object'):
    """Convert a dictionary, list or Collection to an JSON string.

    Args:
        obj: The object to serialize.

    Returns:
        A json string.
    """
    if root:
        obj = { root: obj }
    return json.dumps(obj)


def json_to_dict(jsonstr):
    """Parse the json into a dictionary of attributes.

    Args:
        jsonstr: A JSON formatted string.
    Returns:
        The deserialized object.
    """
    return json.loads(jsonstr)


def _to_xml_element(obj, root, dasherize):
    root = dasherize and root.replace('_', '-') or root
    root_element = ET.Element(root)
    if isinstance(obj, list):
        root_element.set('type', 'array')
        for value in obj:
            root_element.append(_to_xml_element(value, singularize(root), dasherize))
    elif isinstance(obj, dict):
        for key, value in six.iteritems(obj):
            root_element.append(_to_xml_element(value, key, dasherize))
    else:
        serialize(obj, root_element)

    return root_element


def to_xml(obj, root='object', pretty=False, header=True, dasherize=True):
    """Convert a dictionary or list to an XML string.

    Args:
        obj: The dictionary/list object to convert.
        root: The name of the root xml element.
        pretty: Whether to pretty-format the xml (default False).
        header: Whether to include an xml header (default True).
        dasherize: Whether to convert underscores to dashes in
                   attribute names (default True).
    Returns:
        An xml string.
    """
    root_element = _to_xml_element(obj, root, dasherize)
    if pretty:
        xml_pretty_format(root_element)
    xml_data = ET.tostring(root_element)
    if header:
        return XML_HEADER + xml_data
    return xml_data


def xml_to_dict(xmlobj, saveroot=True):
    """Parse the xml into a dictionary of attributes.

    Args:
        xmlobj: An ElementTree element or an xml string.
        saveroot: Keep the xml element names (ugly format)
    Returns:
        An ElementDict object or ElementList for multiple objects
    """
    if isinstance(xmlobj, (six.text_type, six.binary_type)):
        # Allow for blank (usually HEAD) result on success
        if xmlobj.isspace():
            return {}
        try:
            element = ET.fromstring(xmlobj)
        except Exception as err:
            raise Error('Unable to parse xml data: %s' % err)
    else:
        element = xmlobj

    element_type = element.get('type', '').lower()
    if element_type == 'array':
        element_list_type = element.tag.replace('-', '_')
        return_list = element_containers.ElementList(element_list_type)
        for child in list(element):
            return_list.append(xml_to_dict(child, saveroot=False))
        if saveroot:
            return element_containers.ElementDict(element_list_type,
                                                  {element_list_type:
                                                   return_list})
        else:
            return return_list
    elif element.get('nil') == 'true':
        return None
    elif element_type in ('integer', 'datetime', 'date',
                          'decimal', 'double', 'float') and not element.text:
        return None
    elif element_type == 'integer':
        return int(element.text)
    elif element_type == 'datetime':
        if date_parse:
            return date_parse(element.text)
        else:
            try:
                timestamp = calendar.timegm(
                        time.strptime(element.text, '%Y-%m-%dT%H:%M:%S+0000'))

                return datetime.datetime.utcfromtimestamp(timestamp)
            except ValueError as err:
                raise Error('Unable to parse timestamp. Install dateutil'
                            ' (http://labix.org/python-dateutil) or'
                            ' pyxml (http://pyxml.sf.net/topics/)'
                            ' for ISO8601 support.')
    elif element_type == 'date':
        time_tuple = time.strptime(element.text, '%Y-%m-%d')
        return datetime.date(*time_tuple[:3])
    elif element_type == 'decimal':
        return decimal.Decimal(element.text)
    elif element_type in ('float', 'double'):
        return float(element.text)
    elif element_type == 'boolean':
        if not element.text:
            return False
        return element.text.strip() in ('true', '1')
    elif element_type == 'yaml':
        if not yaml:
            raise ImportError('PyYaml is not installed: http://pyyaml.org/')
        return yaml.safe_load(element.text)
    elif element_type == 'base64binary':
        return base64.b64decode(element.text.encode('ascii'))
    elif element_type == 'file':
        content_type = element.get('content_type',
                                   'application/octet-stream')
        filename = element.get('name', 'untitled')
        return FileObject(element.text, filename, content_type)
    elif element_type in ('symbol', 'string'):
        if not element.text:
            return ''
        return element.text
    elif list(element):
        # This is an element with children. The children might be simple
        # values, or nested hashes.
        if element_type:
            attributes = element_containers.ElementDict(
                underscore(element.get('type', '')), element.items())
        else:
            attributes = element_containers.ElementDict(singularize(
                element.tag.replace('-', '_')), element.items())
        for child in list(element):
            attribute = xml_to_dict(child, saveroot=False)
            child_tag = child.tag.replace('-', '_')
            # Handle multiple elements with the same tag name
            if child_tag in attributes:
                if isinstance(attributes[child_tag], list):
                    attributes[child_tag].append(attribute)
                else:
                    attributes[child_tag] = [attributes[child_tag],
                                             attribute]
            else:
                attributes[child_tag] = attribute
        if saveroot:
            return {element.tag.replace('-', '_'): attributes}
        else:
            return attributes
    elif element.items():
        return element_containers.ElementDict(element.tag.replace('-', '_'),
                                              element.items())
    else:
        return element.text
