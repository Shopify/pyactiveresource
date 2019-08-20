#!/usr/bin/python2.4
# Copyright 2008 Google Inc. All Rights Reserved.

'''Tests for collection objects.'''

__author__ = 'Alex Richter (alex.richter@shopify.com)'


import unittest
# from six import BytesIO
# from six.moves import urllib
# from pyactiveresource import connection
# from pyactiveresource import util
# from pyactiveresource import formats
# from pyactiveresource.testing import http_fake
from pyactiveresource.collection import Collection

class CollectionTest(unittest.TestCase):
  def setUp(self):
    self.collection = Collection()

  def test_collection_respond_to_collected(self):
    self.assertTrue(hasattr(self.collection, 'collected'))

  def test_collection_repond_to_to_list(self):
    self.assertTrue(hasattr(self.collection, 'to_list'))

  def test_collection_respond_to_original_params(self):
    self.assertTrue(hasattr(self.collection, 'original_params'))

  def test_collection_respond_to_elements(self):
    self.assertTrue(hasattr(self.collection, 'elements'))

  def test_collected_modifies_elements(self):
    elements = ['Foo', 'Bar']
    func = lambda element : "%s!" % element
    self.collection.elements = elements
    results = self.collection.collected(func)
    
    self.assertEqual(Collection(['Foo!', 'Bar!']), results)

  def test_collected_returns_collection_type(self):
    elements = ['Foo', 'Bar']
    func = lambda element : "%s!" % element
    self.collection.elements = elements
    results = self.collection.collected(func)

    self.assertTrue((type(results) == Collection))

  def test_to_list_returns_list_type(self):
    self.assertEqual(self.collection.to_list(), [])

if __name__ == '__main__':
  unittest.main()