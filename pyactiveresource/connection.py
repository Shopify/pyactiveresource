# Copyright 2008 Google, Inc. All Rights Reserved.

"""A connection object to interface with REST services."""

import base64
import logging
import socket
import sys
import six
from six.moves import urllib
from pyactiveresource import formats


class Error(Exception):
    """A general error derived from Exception."""

    def __init__(self, msg=None, url=None, code=None):
        Exception.__init__(self, msg)
        self.url = url
        self.code = code


class ServerError(Error):
    """An error caused by an ActiveResource server."""
    # HTTP error code 5xx (500..599)

    def __init__(self, response=None):
        if response is not None:
            Error.__init__(self, response.msg, response.url, response.code)
        else:
            Error.__init__(self)


class ConnectionError(Error):
    """An error caused by network connection."""

    def __init__(self, response=None, message=None):
        if not response:
            self.response = Response(None, '')
            url = None
        else:
            self.response = Response.from_httpresponse(response)
            url = response.url
        if not message:
            message = str(self.response)

        Error.__init__(self, message, url, self.response.code)


class Redirection(ConnectionError):
    """HTTP 3xx redirection."""
    pass


class ClientError(ConnectionError):
    """An error caused by an ActiveResource client."""
    # HTTP error 4xx (401..499)
    pass


class ResourceConflict(ClientError):
    """An error raised when there is a resource conflict."""
    # 409 Conflict
    pass


class ResourceInvalid(ClientError):
    """An error raised when a resource is invalid."""
    # 422 Resource Invalid
    pass


class ResourceNotFound(ClientError):
    """An error raised when a resource is not found."""
    # 404 Resource Not Found

    def __init__(self, response=None, message=None):
        if response is not None and message is None:
            message = '%s: %s' % (response.msg, response.url)

        ClientError.__init__(self, response=response, message=message)


class BadRequest(ClientError):
    """An error raised when client sends a bad request."""
    # 400 Bad Request
    pass


class UnauthorizedAccess(ClientError):
    """An error raised when an access is unauthorized."""
    # 401 Unauthorized
    pass


class ForbiddenAccess(ClientError):
    """An error raised when access is not allowed."""
    # 403 Forbidden
    pass


class MethodNotAllowed(ClientError):
    """An error raised when a method is not allowed."""
    # 405 Method Not Allowed
    pass


class Request(urllib.request.Request):
    """A request object which allows additional methods."""

    def __init__(self, *args, **kwargs):
        self._method = None
        urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        """Return the HTTP method."""
        if not self._method:
            return urllib.request.Request.get_method(self)
        return self._method

    def set_method(self, method):
        """Set the HTTP method."""
        self._method = method


def _urllib_has_timeout():
  """Determines if our version of urllib.request.urlopen has a timeout argument."""
  # NOTE: This is a terrible hack, but there's no other indication that this
  #     argument was added to the function.
  version = sys.version_info
  return version[0] >= 2 and version[1] >= 6


class Response(object):
    """Represents a response from the http server."""

    def __init__(self, code, body, headers=None, msg='', response=None):
        """Initialize a new Response object.

        code, body, headers, msg are retrievable as instance attributes.
        Individual headers can be retrieved using dictionary syntax (i.e.
        response['header'] => value.

        Args:
            code: The HTTP response code returned by the server.
            body: The body of the response.
            headers: A dictionary of HTTP headers.
            msg: The HTTP message (e.g. 200 OK => 'OK').
            response: The original httplib.HTTPResponse (if any).
        """
        self.code = code
        self.msg = msg
        self.body = body
        if headers is None:
            headers = {}
        self.headers = headers
        self.response = response

    def __eq__(self, other):
        if isinstance(other, Response):
            return ((self.code, self.body, self.headers) ==
                    (other.code, other.body, other.headers))
        return False

    def __repr__(self):
        return 'Response(code=%s, body="%s", headers=%s, msg="%s")' % (
            self.code, self.body, self.headers, self.msg)

    def __getitem__(self, key):
        return self.headers[key]

    def get(self, key, value=None):
        return self.headers.get(key, value)

    @classmethod
    def from_httpresponse(cls, response):
        """Create a Response object based on an httplib.HTTPResponse object.

        Args:
            response: An httplib.HTTPResponse object.
        Returns:
            A Response object.
        """
        return cls(response.code, response.read(),
                   dict(response.headers), response.msg, response)


class Connection(object):
    """A connection object to interface with REST services."""

    def __init__(self, site, user=None, password=None, timeout=None,
                 format=formats.JSONFormat):
    
        """Initialize a new Connection object.

        Args:
            site: The base url for connections (e.g. 'http://foo')
            user: username for basic authentication.
            password: password for basic authentication.
            timeout: socket timeout.
            format: format object for en/decoding resource data.
        """

        if site is None:
            raise ValueError("Connection site argument requires site")
        self.site, self.user, self.password = self._parse_site(site)
        self.user = user or self.user or ''
        self.password = password or self.password or ''

        if self.user or self.password:
            self.auth = base64.b64encode(('%s:%s' % (self.user, self.password)).encode('utf-8')).decode('utf-8')
        else:
            self.auth = None
        self.timeout = timeout
        self.log = logging.getLogger('pyactiveresource.connection')
        self.format = format

    def _parse_site(self, site):
        """Retrieve the auth information and base url for a site.

        Args:
            site: The URL to parse.
        Returns:
            A tuple containing (site, username, password).
        """
        parts = urllib.parse.urlparse(site)

        host = parts.hostname
        if parts.port:
            host += ":" + str(parts.port)

        new_site = urllib.parse.urlunparse((parts.scheme, host, '', '', '', ''))
        return (new_site, parts.username, parts.password)

    def _request(self, url):
        """Return a new request object.

        Args:
            url: The url to connect to.
        Returns:
            A Request object.
        """
        return Request(url)

    def _open(self, method, path, headers=None, data=None):
        """Perform an HTTP request.

        Args:
            method: The HTTP method (GET, PUT, POST, DELETE).
            path: The HTTP path to retrieve.
            headers: A dictionary of HTTP headers to add.
            data: The data to send as the body of the request.
        Returns:
             A Response object.
        """
        url = urllib.parse.urljoin(self.site, path)
        self.log.info('%s %s', method, url)
        request = self._request(url)
        request.set_method(method)
        if headers:
            for key, value in six.iteritems(headers):
                request.add_header(key, value)
        if self.auth:
            # Insert basic authentication header
            request.add_header('Authorization', 'Basic ' + self.auth)
        if request.headers:
            header_string = '\n'.join([':'.join((k, v)) for k, v in
                                       six.iteritems(request.headers)])
            self.log.debug('request-headers:%s', header_string)
        if data:
            request.add_header('Content-Type', self.format.mime_type)
            request.data = data
            self.log.debug('request-body:%s', request.data)
        elif method in ['POST', 'PUT']:
          # Some web servers need a content length on all POST/PUT operations
          request.add_header('Content-Type', self.format.mime_type)
          request.add_header('Content-Length', '0')

        if self.timeout and not _urllib_has_timeout():
            # Hack around lack of timeout option in python < 2.6
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(self.timeout)
        try:
            http_response = None
            try:
                http_response = self._handle_error(self._urlopen(request))
            except urllib.error.HTTPError as err:
                http_response = self._handle_error(err)
            except urllib.error.URLError as err:
                raise Error(err, url)
            response = Response.from_httpresponse(http_response)
            self.log.debug('Response(code=%d, headers=%s, msg="%s")',
                           response.code, response.headers, response.msg)
        finally:
            if http_response:
                http_response.close()
            if self.timeout and not _urllib_has_timeout():
                socket.setdefaulttimeout(old_timeout)

        self.log.info('--> %d %s %db', response.code, response.msg,
                      len(response.body))
        return response

    def _urlopen(self, request):
        """Wrap calls to urllib so they can be overriden.

        Args:
            request: A Request object.
        Returns:
            An httplib.HTTPResponse object.
        Raises:
            urllib.error.HTTPError on server errors.
            urllib.error.URLError on IO errors.
        """
        if _urllib_has_timeout():
          return urllib.request.urlopen(request, timeout=self.timeout)
        else:
          return urllib.request.urlopen(request)

    def get(self, path, headers=None):
        """Perform an HTTP get request.

        Args:
            path: The HTTP path to retrieve.
            headers: A dictionary of HTTP headers to add.
        Returns:
            A dictionary representing a resource.
        """
        return self.format.decode(self._open('GET', path, headers=headers).body)

    def delete(self, path, headers=None):
        """Perform an HTTP delete request.

        Args:
            path: The HTTP path to retrieve.
            headers: A dictionary of HTTP headers to add.
        Returns:
            A Response object.
        """
        return self._open('DELETE', path, headers=headers)

    def put(self, path, headers=None, data=None):
        """Perform an HTTP put request.

        Args:
            path: The HTTP path to retrieve.
            headers: A dictionary of HTTP headers to add.
            data: The data to send as the body of the request.
        Returns:
            A Response object.
        """
        return self._open('PUT', path, headers=headers, data=data)

    def post(self, path, headers=None, data=None):
        """Perform an HTTP post request.

        Args:
            path: The HTTP path to retrieve.
            headers: A dictionary of HTTP headers to add.
            data: The data to send as the body of the request.
        Returns:
            A Response object.
        """
        return self._open('POST', path, headers=headers, data=data)

    def head(self, path, headers=None):
        """Perform an HTTP put request.

        Args:
            path: The HTTP path to retrieve.
            headers: A dictionary of HTTP headers to add.
        Returns:
            A Response object.
        """
        return self._open('HEAD', path, headers=headers)

    def _handle_error(self, err):
        """Handle an HTTP error.

        Args:
            err: A urllib.error.HTTPError object.
        Returns:
            An HTTP response object if the error is recoverable.
        Raises:
            Redirection: if HTTP error code 301,302 returned.
            BadRequest: if HTTP error code 400 returned.
            UnauthorizedAccess: if HTTP error code 401 returned.
            ForbiddenAccess: if HTTP error code 403 returned.
            ResourceNotFound: if HTTP error code 404 is returned.
            MethodNotAllowed: if HTTP error code 405 is returned.
            ResourceConflict: if HTTP error code 409 is returned.
            ResourceInvalid: if HTTP error code 422 is returned.
            ClientError: if HTTP error code falls in 401 - 499.
            ServerError: if HTTP error code falls in 500 - 599.
            ConnectionError: if unknown HTTP error code returned.
        """
        if err.code in (301, 302):
            raise Redirection(err)
        elif 200 <= err.code < 400:
            return err
        elif err.code == 400:
            raise BadRequest(err)
        elif err.code == 401:
            raise UnauthorizedAccess(err)
        elif err.code == 403:
            raise ForbiddenAccess(err)
        elif err.code == 404:
            raise ResourceNotFound(err)
        elif err.code == 405:
            raise MethodNotAllowed(err)
        elif err.code == 409:
            raise ResourceConflict(err)
        elif err.code == 422:
            raise ResourceInvalid(err)
        elif 401 <= err.code < 500:
            raise ClientError(err)
        elif 500 <= err.code < 600:
            raise ServerError(err)
        else:
            raise ConnectionError(err)
