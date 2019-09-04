import unittest

from pyactiveresource.collection import Collection

class CollectionTest(unittest.TestCase):

    def setUp(self):
        self.collection = Collection([1, 2, 3])

    def test_collection_is_list(self):

        self.assertIsInstance(self.collection, list,
                              "Collection isn't a list instance")

    def test_collection_copy(self):
        a = self.collection.copy()

        self.assertNotEqual(id(self.collection), id(a),
                            "Collection.copy did not copy")
        self.assertEqual(self.collection, a, "Collection's copy is not equal")
        self.assertEqual(self.collection.metadata, a.metadata,
                         "Metadata isn't equal")

    def test_collection_iteration(self):
        i = iter(self.collection)

        self.assertEqual(next(i), 1)
        self.assertEqual(next(i), 2)
        self.assertEqual(next(i), 3)
        with self.assertRaises(StopIteration):
            next(i)

    def test_collection_metadata(self):
        a = Collection([], metadata={
            "foo": "bar"
        })

        self.assertEqual(a.metadata["foo"], "bar",
                         "Metadata from constructor doesn't work")

        a.metadata["baz"] = "quux"
        self.assertEqual(a.metadata["baz"], "quux",
                         "Metadata mutation doesn't work")

        b = a.copy()
        b.metadata["foo"] = "notbar"
        self.assertNotEqual(a.metadata["foo"], "notbar",
                            "Metadata isn't deep copied")


    def test_collection_iterator_constructor(self):
        a = Collection(i for i in range(1, 4))

        self.assertEqual(self.collection, a,
                         "Iterator constructor didn't create proper Collection")

    def test_collection_list_equality(self):
        l = [1, 2, 3]

        self.assertEqual(self.collection, l,
                         "Collection isn't equal to list with same contents")
