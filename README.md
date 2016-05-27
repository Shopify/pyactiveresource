PyActiveResource
================

A python port of the [ActiveResource
](https://github.com/rails/activeresource) project,
which provides an object-relational mapping for REST web services.

Development prior to 2014 took place here:
https://code.google.com/p/pyactiveresource/

Development going forward will take place on [Github](https://github.com/Shopify/pyactiveresource). Please
submit new issues and patches there.

[pyactiveresource mailing list](https://groups.google.com/forum/#!forum/pyactiveresource)

Philosophy
------------
Active Resource attempts to provide a coherent wrapper object-relational mapping for REST web services. It follows the same philosophy as Active Record, in that one of its prime aims is to reduce the amount of code needed to map to these resources. This is made possible by relying on a number of code- and protocol-based conventions that make it easy for Active Resource to infer complex relations and structures. These conventions are outlined in detail in the documentation for ActiveResource::Base.

Overview
------------
Model classes are mapped to remote REST resources by Active Resource much the same way Active Record maps model classes to database tables. When a request is made to a remote resource, a REST JSON request is generated, transmitted, and the result received and serialized into a usable Ruby object.

Installation
------------

To install or upgrade to the latest released version

    pip install --upgrade pyactiveresource

To install this package from source

    python setup.py install

Configuration and Usage
-----------------------
Using pyActiveResource is simple. First create a new class that inherits from and provide a site class variable to it:
```
# Import active resource
from pyactiveresource import activeresource as ar

# extend active resource and add the _site var to point to the REST endpoint
class Person(ar.ActiveResource):
  _site =  'http://api.people.com:3000/people'
```

Now the class is rest enabled each request is made on the class and responses spawn new object representing the response as a resource.

Authentication/Headers
----------------------
You can set headers for each request with the _header class variable. This allows you to pass information to the REST endpoint such as auth tokens

```
class Person(ar.ActiveResource):
  _site =  'http://api.people.com:3000/people'
  _headers = { 'auth': token }

```

Protocol
--------
pyActiveResource is built on a standard JSON format for requesting and submiting resources over HTTP. It mirrors the RESTful routing protocol. REST uses HTTP, but unlike "Typical" web applications, it makes uses of all available HTTP verbs from the specifaction.

* GET requests are used to find and retrieve resources.
* POST requests are used to create new resources.
* PUT requests are used to update existing resources.
* DELETE requests are used to delete resources.

For more information on how this protocol works see the article [here](https://en.wikipedia.org/wiki/Representational_state_transfer).

Find
----
Find requests use the GET method and expect the JSON form of whatever resource/resources is/are being requested. So, for a request for a single element, the JSON of that item is expected in response:
```
# Expects a response of
#
# {"id":1,"first":"Tyler","last":"Durden"}
#
# for GET http://api.people.com:3000/people/1.json
#
person = Person.find(1) # person will be an object with the json keys mapped to attributes of the object
```

The JSON document that is received is used to build a new object of type Person, with each JSON element becoming an attribute on the object.
```
person.first # Tyler
type(person) # Person
```

Any complex element (one that contains other elements) becomes its own object:
```
# With this response:
# {"id":1,"first":"Tyler","address":{"street":"Paper St.","state":"CA"}}
#
# for GET http://api.people.com:3000/people/1.json
#
tyler = Person.find(1)
type(tyler.address)  # Address
tyler.address.street  # 'Paper St.'
```

Collections can also be requested in a similar fashion
```
# Expects a response of
#
# [
#   {"id":1,"first":"Tyler","last":"Durden"},
#   {"id":2,"first":"Tony","last":"Stark",}
# ]
#
# for GET http://api.people.com:3000/people.json
#
people = Person.find()
people[0].first  # 'Tyler'
people[1].first  # 'Tony
```

You can append url params to the request by passing in a dictionary of the required params.
```
# for GET http://api.people.com:3000/people.json?page=30&member=true
#
people = Person.find(page=30, member='true')

```

Create
------
Creating a new resource submits the JSON form of the resource as the body of the request and expects a 'Location' header in the response with the RESTful URL location of the newly created resource. The id of the newly created resource is parsed out of the Location response header and automatically set as the id of the object.
```
# {"first":"Tyler","last":"Durden"}
#
# is submitted as the body on
#
# POST http://api.people.com:3000/people.json
#
# when save is called on a new Person object.  An empty response is
# is expected with a 'Location' header value:
#
# Response (201): Location: http://api.people.com:3000/people/2
#
tyler = Person.create({ 'first': 'Tyler' })
tyler.id    # 2
```

Update
------
'save' is also used to update an existing resource and follows the same protocol as creating a resource with the exception that no response headers are needed – just an empty response when the update on the server side was successful.
```
# {"first":"Tyler"}
#
# is submitted as the body on
#
# PUT http://api.people.com:3000/people/1.json
#
# when save is called on an existing Person object.  An empty response is
# is expected with code (204)
#
tyler.first = 'Tyson'
tyler.save()  # true
```

Delete
-----
Destruction of a resource can be invoked as a class and instance method of the resource.
```
# A request is made to
#
# DELETE http://api.people.com:3000/people/1.json
#
# for both of these forms.  An empty response with
# is expected with response code (200)
#
tyler.delete()
```

Running Tests
-------------

Run the following from the top level directory

    python setup.py test
