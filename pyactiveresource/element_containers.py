# Copyright 2010 Google Inc. All Rights Reserved.

__author__ = 'danv@google.com (Daniel Van Derveer)'

class ElementList(list):
  """A list object with an element_type attribute."""

  def __init__(self, element_type, *args):
    """Constructor for ElementList."""
    self.element_type = element_type
    super(ElementList, self).__init__(*args)


class ElementDict(dict):
  """A dictionary object with an element_type attribute."""

  def __init__(self, element_type, *args):
    """Constructor for ElementDict."""
    self.element_type = element_type
    super(ElementDict, self).__init__(*args)
