class Collection(list):
  def __init__(self, elements=[], original_params={}):
    self.elements = elements
    self.original_params = original_params
    super(list)

  @property
  def original_params(self):
    return self._original_params

  @original_params.setter
  def original_params(self, params):
    self._original_params = params
    return self

  def to_list(self):
    return self.elements

  def collected(self, func=None):
    result = []
    if not func:
      return self.elements

    for element in self.elements:
      result.append(func(element))

    self.elements = result
    return self
