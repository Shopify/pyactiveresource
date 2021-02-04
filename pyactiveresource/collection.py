import copy

class Collection(list):
    """
    Defines a collection of objects.

    The collection holds extra metadata about the objects which are used
    in things like pagination.
    """

    def __init__(self, *args, **kwargs):
        self._metadata = kwargs.pop("metadata", {})
        super(Collection, self).__init__(*args, **kwargs)

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def copy(self):
        """Override list.copy so that it returns a Collection."""
        copied_list = list(self)
        return Collection(copied_list, metadata=copy.deepcopy(self._metadata))

    def __eq__(self, other):
        """Test equality of metadata as well as the items."""

        same_list = super(Collection, self).__eq__(other)
        if isinstance(other, Collection):
            return same_list and self.metadata == other.metadata
        if isinstance(other, list):
            return same_list
        return False
