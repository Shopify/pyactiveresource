#!/usr/bin/python2.4
# Copyright 2008 Google Inc. All Rights Reserved.

"""Tests for util functions."""

__author__ = 'Mark Roach (mrroach@google.com)'

import datetime
import decimal
import unittest
import six
from pyactiveresource import util
from pprint import pprint


def diff_dicts(d1, d2):
    """Print the differences between two dicts. Useful for troubleshooting."""
    pprint([(k,v) for k,v in d2.items()
            if v != d1[k]])


class UtilTest(unittest.TestCase):
    def setUp(self):
        """Create test objects."""

    def test_xml_to_dict_single_record(self):
        """Test the xml_to_dict function."""
        topic_xml = '''<topic>
             <title>The First Topic</title>
             <author-name>David</author-name>
             <id type="integer">1</id>
             <approved type="boolean"> true </approved>
             <replies-count type="integer">0</replies-count>
             <replies-close-in type="integer">2592000000</replies-close-in>
             <written-on type="date">2003-07-16</written-on>
             <viewed-at type="datetime">2003-07-16T09:28:00+0000</viewed-at>
             <content type="yaml">--- \n1: should be an integer\n:message: Have a nice day\narray: \n- should-have-dashes: true\n  should_have_underscores: true\n</content>
             <author-email-address>david@loudthinking.com</author-email-address>
             <parent-id></parent-id>
             <ad-revenue type="decimal">1.5</ad-revenue>
             <optimum-viewing-angle type="float">135</optimum-viewing-angle>
             <resident type="symbol">yes</resident>
           </topic>'''

        expected_topic_dict = {
            'title': 'The First Topic',
            'author_name': 'David',
            'id': 1,
            'approved': True,
            'replies_count': 0,
            'replies_close_in': 2592000000,
            'written_on': datetime.date(2003, 7, 16),
            'viewed_at': util.date_parse('2003-07-16T9:28Z'),
            'content': {':message': 'Have a nice day',
                        1: 'should be an integer',
                        'array': [{'should-have-dashes': True,
                                   'should_have_underscores': True}]},
            'author_email_address': 'david@loudthinking.com',
            'parent_id': None,
            'ad_revenue': decimal.Decimal('1.5'),
            'optimum_viewing_angle': 135.0,
            'resident': 'yes'}

        self.assertEqual(expected_topic_dict, util.xml_to_dict(topic_xml, saveroot=False))
        self.assertEqual(expected_topic_dict,
                         util.xml_to_dict(topic_xml)['topic'])

    def test_xml_to_dict_multiple_records(self):
        """Test the xml to dict function."""
        topics_xml = '''<topics type="array">
            <topic>
              <title>The First Topic</title>
              <author-name>David</author-name>
              <id type="integer">1</id>
              <approved type="boolean">false</approved>
              <replies-count type="integer">0</replies-count>
              <replies-close-in type="integer">2592000000</replies-close-in>
              <written-on type="date">2003-07-16</written-on>
              <viewed-at type="datetime">2003-07-16T09:28:00+0000</viewed-at>
              <content>Have a nice day</content>
              <author-email-address>david@loudthinking.com</author-email-address>
              <parent-id nil="true"></parent-id>
            </topic>
            <topic>
              <title>The Second Topic</title>
              <author-name>Jason</author-name>
              <id type="integer">1</id>
              <approved type="boolean">false</approved>
              <replies-count type="integer">0</replies-count>
              <replies-close-in type="integer">2592000000</replies-close-in>
              <written-on type="date">2003-07-16</written-on>
              <viewed-at type="datetime">2003-07-16T09:28:00+0000</viewed-at>
              <content>Have a nice day</content>
              <author-email-address>david@loudthinking.com</author-email-address>
              <parent-id></parent-id>
            </topic>
          </topics>'''

        expected_topic_dict = {
          'title': 'The First Topic',
          'author_name': 'David',
          'id': 1,
          'approved': False,
          'replies_count': 0,
          'replies_close_in': 2592000000,
          'written_on': datetime.date(2003, 7, 16),
          'viewed_at': util.date_parse('2003-07-16T09:28Z'),
          'content': 'Have a nice day',
          'author_email_address': 'david@loudthinking.com',
          'parent_id': None}

        self.assertEqual(expected_topic_dict,
                         util.xml_to_dict(topics_xml, saveroot=False)[0])
        self.assertEqual(
                expected_topic_dict,
                util.xml_to_dict(topics_xml, saveroot=True)['topics'][0])

    def test_xml_to_dict_multiple_records_with_different_types(self):
        """Test the xml to dict function."""
        topics_xml = '''<topics type="array">
            <topic>
              <title>The First Topic</title>
              <author-name>David</author-name>
              <id type="integer">1</id>
              <approved type="boolean">false</approved>
              <replies-count type="integer">0</replies-count>
              <replies-close-in type="integer">2592000000</replies-close-in>
              <written-on type="date">2003-07-16</written-on>
              <viewed-at type="datetime">2003-07-16T09:28:00+0000</viewed-at>
              <content>Have a nice day</content>
              <author-email-address>david@loudthinking.com</author-email-address>
              <parent-id nil="true"></parent-id>
            </topic>
            <topic type='SubTopic'>
              <title>The Second Topic</title>
              <author-name>Jason</author-name>
              <id type="integer">1</id>
              <approved type="boolean">false</approved>
              <replies-count type="integer">0</replies-count>
              <replies-close-in type="integer">2592000000</replies-close-in>
              <written-on type="date">2003-07-16</written-on>
              <viewed-at type="datetime">2003-07-16T09:28:00+0000</viewed-at>
              <content>Have a nice day</content>
              <author-email-address>david@loudthinking.com</author-email-address>
              <parent-id></parent-id>
            </topic>
          </topics>'''

        parsed = util.xml_to_dict(topics_xml, saveroot=False)
        self.assertEqual('topics', parsed.element_type)
        self.assertEqual('topic', parsed[0].element_type)
        self.assertEqual('sub_topic', parsed[1].element_type)


    def test_xml_to_dict_empty_array(self):
        blog_xml = '''<blog>
            <posts type="array"></posts>
            </blog>'''
        expected_blog_dict = {'blog': {'posts': []}}
        self.assertEqual(expected_blog_dict,
                         util.xml_to_dict(blog_xml, saveroot=True))

    def test_xml_to_dict_empty_array_with_whitespace(self):
        blog_xml = '''<blog>
            <posts type="array">
            </posts>
          </blog>'''
        expected_blog_dict = {'blog': {'posts': []}}
        self.assertEqual(expected_blog_dict,
                         util.xml_to_dict(blog_xml, saveroot=True))

    def test_xml_to_dict_array_with_one_entry(self):
        blog_xml = '''<blog>
            <posts type="array">
              <post>a post</post>
            </posts>
          </blog>'''
        expected_blog_dict = {'blog': {'posts': ['a post']}}
        self.assertEqual(expected_blog_dict,
                         util.xml_to_dict(blog_xml, saveroot=True))

    def test_xml_to_dict_file(self):
        blog_xml = '''<blog>
            <logo type="file" name="logo.png" content_type="image/png">
            </logo>
          </blog>'''
        blog_dict = util.xml_to_dict(blog_xml, saveroot=True)
        self.assert_('blog' in blog_dict)
        self.assert_('logo' in blog_dict['blog'])
        blog_file = blog_dict['blog']['logo']
        self.assertEqual('logo.png', blog_file.name)
        self.assertEqual('image/png', blog_file.content_type)


    def test_xml_to_dict_file_with_defaults(self):
        blog_xml = '''<blog>
            <logo type="file">
            </logo>
          </blog>'''
        blog_dict = util.xml_to_dict(blog_xml, saveroot=True)
        self.assert_('blog' in blog_dict)
        self.assert_('logo' in blog_dict['blog'])
        blog_file = blog_dict['blog']['logo']
        self.assertEqual('untitled', blog_file.name)
        self.assertEqual('application/octet-stream', blog_file.content_type)

    def test_xml_to_dict_xsd_like_types(self):
        bacon_xml = '''<bacon>
            <weight type="double">0.5</weight>
            <price type="decimal">12.50</price>
            <chunky type="boolean"> 1 </chunky>
            <expires-at type="dateTime">2007-12-25T12:34:56+0000</expires-at>
            <notes type="string"></notes>
            <illustration type="base64Binary">YmFiZS5wbmc=</illustration>
            </bacon>'''
        expected_bacon_dict = {
            'weight': 0.5,
            'chunky': True,
            'price': decimal.Decimal('12.50'),
            'expires_at': util.date_parse('2007-12-25T12:34:56Z'),
            'notes': '',
            'illustration': b'babe.png'}

        self.assertEqual(expected_bacon_dict,
                         util.xml_to_dict(bacon_xml, saveroot=True)['bacon'])

    def test_xml_to_dict_should_parse_dictionaries_with_unknown_types(self):
        xml = '''<records type="array">
                   <record type="MiscData">
                     <name>misc_data1</name>
                   </record>
                 </records>'''
        expected = {'records': [{'type': 'MiscData', 'name': 'misc_data1'}]}
        self.assertEqual(expected, util.xml_to_dict(xml, saveroot=True))

    def test_xml_to_dict_should_include_xml_attributes_as_dictionary_items(self):
        xml = '''<record><child name="child_name" id="1234" /></record>'''
        result = util.xml_to_dict(xml, saveroot=True)
        self.assertEqual('child_name', result['record']['child']['name'])
        self.assertEqual('1234', result['record']['child']['id'])

    def test_xml_to_dict_parses_datetime_timezones(self):
        blog_xml = '''<blog>
            <posted_at type="datetime">2008-09-05T13:34-0700</posted_at>
          </blog>'''
        blog_dict = util.xml_to_dict(blog_xml, saveroot=True)
        self.assertEqual((2008, 9, 5, 20, 34, 0, 4, 249, 0),
                         blog_dict['blog']['posted_at'].utctimetuple())

    def test_xml_to_dict_unknown_type(self):
        product_xml = '''<product>
            <weight type="double">0.5</weight>
            <image type="ProductImage"><filename>image.gif</filename></image>
           </product>'''
        expected_product_dict = {
            'weight': 0.5,
            'image': {'type': 'ProductImage', 'filename': 'image.gif'}}
        self.assertEqual(
                expected_product_dict,
                util.xml_to_dict(product_xml, saveroot=True)['product'])

    def test_xml_to_dict_errors_on_empty_string(self):
        self.assertRaises(Exception, util.xml_to_dict, '')

    def test_xml_to_dict_parses_children_which_are_not_of_parent_type(self):
        product_xml = '''
          <products type="array">
            <shamwow><made-in>Germany</made-in></shamwow>
          </products>'''
        self.assertEqual({'products': [{'made_in': 'Germany'}]},
                         util.xml_to_dict(product_xml, saveroot=True))

    def test_to_xml_should_allow_unicode(self):
        xml = util.to_xml({'data': u'\xe9'})
        self.assert_(b'<data>&#233;</data>' in xml)

    if six.PY2:
        def test_to_xml_should_allow_utf8_encoded_strings(self):
            xml = util.to_xml({'data': u'\xe9'.encode('utf-8')})
            self.assert_(b'<data>&#233;</data>' in xml)
    else:
        def test_to_xml_should_encode_bytes_as_base64(self):
            xml = util.to_xml({'data': b'\xe9'})
            self.assert_(b'<data type="base64Binary">6Q==</data>' in xml)

    def test_to_xml_should_allow_disabling_dasherization(self):
        xml = util.to_xml({'key_name': 'value'}, dasherize=False)
        self.assert_(b'<key_name>value</key_name>' in xml)

    def test_to_xml_should_honor_dasherize_option_for_children(self):
        xml = util.to_xml([{'key_name': 'value'}], dasherize=False)
        self.assert_(b'<key_name>value</key_name>' in xml)

    def test_to_xml_should_consider_attributes_on_element_with_children(self):
        custom_field_xml = '''
            <custom_field name="custom1" id="1">
              <value>cust1</value>
            </custom_field>'''
        expected = {
                'custom_field': {
                    'name': 'custom1',
                    'id': '1',
                    'value': 'cust1'}
                }
        result = util.xml_to_dict(custom_field_xml, saveroot=True)
        self.assertEqual(expected, result)

    def test_to_query_with_utf8_encoded_strings(self):
        query = util.to_query({'var': b'\xC3\xA5\xC3\xB1\xC3\xBC\xC3\xA8'})
        self.assertEqual('var=%C3%A5%C3%B1%C3%BC%C3%A8', query)

    def test_to_query_with_unicode_strings(self):
        query = util.to_query({'var': u'\xe5\xf1\xfc\xe8'})
        self.assertEqual('var=%C3%A5%C3%B1%C3%BC%C3%A8', query)

    def test_to_query_with_arrays(self):
        query = util.to_query({'var': ['a', 2, 3.0]})
        self.assertEqual('var%5B%5D=a&var%5B%5D=2&var%5B%5D=3.0', query)

    def test_to_query_with_dictionaries(self):
        query = util.to_query({'var': {'a': 1, 'b':{'c': 2}}})
        self.assertEqual(set(['var%5Ba%5D=1', 'var%5Bb%5D%5Bc%5D=2']), set(query.split('&')))

    def test_json_to_dict_single_record(self):
        """Test the json_to_dict function."""
        topic_json = '''{
              "topic": {
                "title": "The First Topic",
                "author_name": "David",
                "id": 1,
                "approved": true,
                "replies_count": 0,
                "replies_close_in": 2592000000,
                "written_on": "2003-07-16",
                "viewed_at": "2003-07-16T09:28:00+0000",
                "content": "--- \\n1: should be an integer\\n:message: Have a nice day\\narray: \\n- should-have-dashes: true\\n  should_have_underscores: true\\n",
                "author_email_address": "david@loudthinking.com",
                "parent_id": null,
                "ad_revenue": 1.5,
                "optimum_viewing_angle": 135.0,
                "resident": "yes"
              }
            }'''

        expected_topic_dict = {
            'title': 'The First Topic',
            'author_name': 'David',
            'id': 1,
            'approved': True,
            'replies_count': 0,
            'replies_close_in': 2592000000,
            'written_on': "2003-07-16",
            'viewed_at': "2003-07-16T09:28:00+0000",
            'content': "--- \n1: should be an integer\n:message: Have a nice day\narray: \n- should-have-dashes: true\n  should_have_underscores: true\n",
            'author_email_address': 'david@loudthinking.com',
            'parent_id': None,
            'ad_revenue': 1.5,
            'optimum_viewing_angle': 135.0,
            'resident': 'yes'
            }

        self.assertEqual(expected_topic_dict,
                         util.json_to_dict(topic_json)['topic'])

    def test_json_to_dict_multiple_records(self):
        """Test the json to dict function."""
        topics_json = '''{
             "topics": [
               { "title": "The First Topic" },
               { "title": "The Second Topic" }
             ]
           }'''

        expected_topic_dicts = [
              { 'title': 'The First Topic' },
              { 'title': 'The Second Topic' },
            ]

        self.assertEqual(expected_topic_dicts,
                         util.json_to_dict(topics_json)['topics'])

    def test_to_json_should_allow_unicode(self):
        json = util.to_json({'data': u'\u00e9'})
        self.assert_('\u00e9' in json or '\\u00e9' in json)

    if six.PY2:
        def test_to_json_should_allow_utf8_encoded_strings(self):
            json = util.to_json({'data': u'\u00e9'.encode('utf-8')})
            self.assert_('\u00e9' in json)

    def test_to_json_with_root(self):
        xml = util.to_xml({'title': 'Test'}, root='product')
        self.assert_(b'product' in xml)


if __name__ == '__main__':
    unittest.main()
