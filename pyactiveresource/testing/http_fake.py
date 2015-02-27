# Copyright 2008 Google Inc. All Rights Reserved.

"""Fake urllib HTTP connection objects."""

__author__ = 'Mark Roach (mrroach@google.com)'


from pprint import pformat
import six
from six import BytesIO
from six.moves import urllib


class Error(Exception):
    """Base exception type for this module."""


def initialize():
    """Install TestHandler as the only active handler for http requests."""
    opener = urllib.request.build_opener(TestHandler)
    urllib.request.install_opener(opener)


def create_response_key(method, url, request_headers):
    """Create the response key for a request.

    Args:
        method: The http method (e.g. 'get', 'put', etc.)
        url: The path being requested including site.
        request_headers: Dictionary of headers passed along with the request.
    Returns:
        The key as a string.
    """
    parsed = urllib.parse.urlsplit(url)
    qs = urllib.parse.parse_qs(parsed.query)
    query = urllib.parse.urlencode([(k, qs[k]) for k in sorted(qs.keys())])
    return str((
        method,
        urllib.parse.urlunsplit((
            parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment)),
        dictionary_to_canonical_str(request_headers)))


def dictionary_to_canonical_str(dictionary):
    """Create canonical string from a dictionary.

    Args:
        dictionary: The dictionary to convert.
    Returns:
        A string of the dictionary in canonical form.
    """
    return str([(k.capitalize(), dictionary[k]) for k in sorted(
        dictionary.keys())])


class TestHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
    """A urllib handler object which returns a predefined response."""

    _response = None
    _response_map = {}
    request = None
    site = ''

    def __init__(self, debuglevel=0, **kwargs):
        self._debuglevel = debuglevel
        self._context = kwargs.get('context')
        self._check_hostname = kwargs.get('check_hostname')

    @classmethod
    def set_response(cls, response):
        """Set a static response to be returned for all requests.

        Args:
            response: A FakeResponse object to be returned.
        """
        cls._response_map = {}
        cls._response = response

    @classmethod
    def respond_to(cls, method, path,
                   request_headers, body, code=200, response_headers=None):
        """Build a response object to be used for a specific request.

        Args:
            method: The http method (e.g. 'get', 'put' etc.)
            path: The path being requested (e.g. '/collection/id.json')
            request_headers: Dictionary of headers passed along with the request
            body: The string that should be returned for a matching request
            code: The http response code to return
            response_headers: Dictionary of headers to return
        Returns:
            None
        """
        key = create_response_key(method, urllib.parse.urljoin(cls.site, path),
                                  request_headers)
        value = (code, body, response_headers)
        cls._response_map[str(key)] = value

    def do_open(self, http_class, request, **http_conn_args):
        """Return the response object for the given request.

        Overrides the HTTPHandler method of the same name to return a
        FakeResponse instead of creating any network connections.

        Args:
            http_class: The http protocol being used.
            request: A urllib.request.Request object.
        Returns:
            A FakeResponse object.
        """
        self.__class__.request = request  # Store the most recent request object
        if self._response_map:
            key = create_response_key(
                request.get_method(), request.get_full_url(), request.headers)
            if str(key) in self._response_map:
                (code, body, response_headers) = self._response_map[str(key)]
                return FakeResponse(code, body, response_headers)
            else:
                raise Error('Unknown request %s %s'
                            '\nrequest:%s\nresponse_map:%s' % (
                            request.get_method(), request.get_full_url(),
                            str(key), pformat(list(self._response_map.keys()))))
        elif isinstance(self._response, Exception):
            raise(self._response)
        else:
            return self._response


class FakeResponse(object):
    """A fake HTTPResponse object for testing."""

    def __init__(self, code, body, headers=None):
        self.code = code
        self.msg = str(code)
        if headers is None:
            headers = {}
        self.headers = headers
        self.info = lambda: self.headers
        if isinstance(body, six.text_type):
            body = body.encode('utf-8')
        self.body_file = BytesIO(body)

    def read(self):
        """Read the entire response body."""
        return self.body_file.read()

    def readline(self):
        """Read a single line from the response body."""
        return self.body_file.readline()

    def close(self):
        """Close the connection."""
        pass
