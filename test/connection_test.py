#!/usr/bin/python2.4
# Copyright 2008 Google Inc. All Rights Reserved.

'''Tests for connection objects.'''

__author__ = 'Mark Roach (mrroach@google.com)'


import unittest
from six import BytesIO
from six.moves import urllib
from pyactiveresource import connection
from pyactiveresource import util
from pyactiveresource import formats
from pyactiveresource.testing import http_fake


class Error(Exception):
    pass


class ConnectionTest(unittest.TestCase):
    def setUp(self):
        '''Create test objects.'''
        matz = {'id': 1, 'name': 'Matz'}
        david = {'id': 2, 'name': 'David'}
        self.matz  = util.to_json(matz, root='person')
        self.david = util.to_json(david, root='person') 
        self.people = util.to_json([matz, david], root='people')
        self.people_single = util.to_json(
            [matz], root='people-single-elements')
        self.people_empty = util.to_json([], root='people-empty-elements')

        http_fake.initialize()
        self.http = http_fake.TestHandler
        self.http.site = 'http://localhost'
        self.http.set_response(Error('Bad request'))

        self.zero_length_content_headers = {'Content-Length': '0',
                                            'Content-Type': 'application/json'}

        self.header = {'Key': 'value'}
        self.connection = connection.Connection(self.http.site)
    
    def assert_response_raises(self, error, code):
        response = urllib.error.HTTPError('', code, '', {}, BytesIO(b''))
        self.http.set_response(response)
        self.assertRaises(error, self.connection._open, '', '')
      
    def test_handle_bad_request(self):
        # 400 is a bad request (e.g. malformed URI or missing request parameter)
        self.assert_response_raises(connection.BadRequest, 400)

    def test_handle_valid_response(self):
        # 2xx and 3xx are valid responses.
        for code in [200, 299, 300, 399]:
            response = http_fake.FakeResponse(code, str(code))
            self.http.set_response(response)
            self.assertEquals(self.connection._open('', ''),
                              connection.Response(code, str(code).encode('utf-8')))

    def test_handle_unauthorized_access(self):
        # 401 is an unauthorized request
        self.assert_response_raises(connection.UnauthorizedAccess, 401)

    def test_handle_forbidden_access(self):
        # 403 is a forbidden requst (and authorizing will not help)
        self.assert_response_raises(connection.ForbiddenAccess, 403)

    def test_handle_resource_not_found(self):
        # 404 is a missing resource.
        self.assert_response_raises(connection.ResourceNotFound, 404)

    def test_handle_method_not_allowed(self):
        # 405 is a missing not allowed error
        self.assert_response_raises(connection.MethodNotAllowed, 405)

    def test_handle_resource_conflict(self):
        # 409 is an optimistic locking error
        self.assert_response_raises(connection.ResourceConflict, 409)

    def test_handle_resource_invalid(self):
        # 422 is a validation error
        self.assert_response_raises(connection.ResourceInvalid, 422)

    def test_handle_client_error(self):
        # 4xx are client errors.
        for code in [402, 499]:
            self.assert_response_raises(connection.ClientError, code)

    def test_handle_server_error(self):
        # 5xx are server errors.
        for code in [500, 599]:
            self.assert_response_raises(connection.ServerError, code)

    def test_handle_connection_error(self):
        # Others are unknown.
        for code in [199, 600]:
            self.assert_response_raises(connection.ConnectionError, code)

    def test_timeout_attribute(self):
        self.connection.timeout = 7
        self.assertEqual(7, self.connection.timeout)

    def test_initialize_raises_argument_error_on_missing_site(self):
        self.assertRaises(Exception, connection.Connection, None)

    def test_get(self):
        person = util.to_json({'id': 1, 'name': 'Matz'}, root='person')
        self.http.respond_to(
            'GET', '/people/1.json', {}, person)
        self.connection.format = formats.JSONFormat
        response = self.connection.get('/people/1.json')
        self.assertEqual(response['name'], 'Matz')

    def test_get_with_xml_format(self):
        person = util.to_xml({'id': 1, 'name': 'Matz'}, root='person')
        self.http.respond_to(
            'GET', '/people/1.xml', {}, person)
        self.connection.format = formats.XMLFormat
        response = self.connection.get('/people/1.xml')
        self.assertEqual(response['name'], 'Matz')

    def test_head(self):
        self.http.respond_to('HEAD', '/people/1.json', {}, '')
        self.assertFalse(self.connection.head('/people/1.json').body)

    def test_get_with_header(self):
        self.http.respond_to(
            'GET', '/people/2.json', self.header, self.david)
        david = self.connection.get('/people/2.json', self.header)
        self.assertEqual(david['name'], 'David')
  
    def test_get_collection(self):
        self.http.respond_to('GET', '/people.json', {}, self.people)
        people = self.connection.get('/people.json')
        self.assertEqual('Matz', people[0]['name'])
        self.assertEqual('David', people[1]['name'])
    
    def test_get_collection_single(self):
        self.http.respond_to('GET', '/people_single_elements.json', {},
                             self.people_single)
        people = self.connection.get('/people_single_elements.json')
        self.assertEqual('Matz', people[0]['name'])
    
    def test_get_collection_empty(self):
        self.http.respond_to('GET', '/people_empty_elements.json', {},
                             self.people_empty)
        people = self.connection.get('/people_empty_elements.json')
        self.assertEqual([], people)

    def test_post(self):
        content_headers = {'Content-Length': '0',
                           'Content-Type': 'application/json'}
        self.http.respond_to(
            'POST', '/people.json', content_headers,
            '', 200, {'Location': '/people/5.json'})
        self.connection.format = formats.JSONFormat
        response = self.connection.post('/people.json')
        self.assertEqual('/people/5.json', response['Location'])

    def test_post_with_xml_format(self):
        content_headers = {'Content-Length': '0',
                           'Content-Type': 'application/xml'}
        self.http.respond_to(
            'POST', '/people.xml', content_headers,
            '', 200, {'Location': '/people/5.xml'})
        self.connection.format = formats.XMLFormat
        response = self.connection.post('/people.xml')
        self.assertEqual('/people/5.xml', response['Location'])

    def test_post_with_header(self):
        header = self.header
        header.update(self.zero_length_content_headers)
        self.http.respond_to(
            'POST', '/members.json', self.header,
            '', 201, {'Location': '/people/6.json'})
        response = self.connection.post('/members.json', self.header)
        self.assertEqual('/people/6.json', response['Location'])

    def test_put(self):
        self.http.respond_to('PUT', '/people/1.json',
                             self.zero_length_content_headers, '', 204)
        response = self.connection.put('/people/1.json')
        self.assertEqual(204, response.code)
  
    def test_put_with_header(self):
        header = self.header
        header.update(self.zero_length_content_headers)
        self.http.respond_to('PUT', '/people/2.json', header, '', 204)
        response = self.connection.put('/people/2.json', self.header)
        self.assertEqual(204, response.code)
  
    def test_delete(self):
        self.http.respond_to('DELETE', '/people/1.json', {}, '')
        response = self.connection.delete('/people/1.json')
        self.assertEqual(200, response.code)
  
    def test_delete_with_header(self):
        self.http.respond_to('DELETE', '/people/2.json', self.header, '')
        response = self.connection.delete('/people/2.json', self.header)
        self.assertEqual(200, response.code)

'''
  ResponseHeaderStub = Struct.new(:code, :message, 'Allow')
  def test_should_return_allowed_methods_for_method_no_allowed_exception
    begin
      handle_response ResponseHeaderStub.new(405, 'HTTP Failed...', 'GET, POST')
    rescue connection.MethodNotAllowed => e
      self.assertEqual('Failed with 405 HTTP Failed...', e.message
      self.assertEqual([:get, :post], e.allowed_methods


  uses_mocha('test_timeout') do
    def test_timeout
      @http = mock('new Net::HTTP')
      self.connection.expects(:http).returns(@http)
      @http.expects(:get).raises(Timeout::Error, 'execution expired')
      assert_raises(connection.TimeoutError) { self.connection.get('/people_timeout.json') }
'''


if __name__ == '__main__':
    unittest.main()
