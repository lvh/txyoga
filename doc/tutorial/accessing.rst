====================================
 Accessing collections and elements
====================================

To introduce txYoga, we're going to start with a simple example of a
bunch of employees who work at a startup (because blogs with articles
are just cliché).

Example code
============

.. literalinclude:: accessing.rpy
   :language: python

First, the code defines a collection class called
``Company``. Collections are containers for elements. The collection
class has an attribute called ``exposedElementAttributes``. These are
the attribute the collection will expose about its elements. In this
case, we want to show the names of our employees when the collection
is queried. Obviously, the elements should have such a ``name``
attribute.

Note the comma at the end: the attribute is an iterable of the
collection names (in this case, a tuple with one element). If you left
it out, txYoga would just see a string, which is *also* an iterable of
strings, but it's quite likely that you don't want to expose the
attributes ``'n', 'a', 'm', 'e'``...

Once the collection is defined, the module defines an element class to
go in the collection. In this example, that's ``Employee``. Its
instances go in instances of the previously defined Company
collection. The element class has an attribute called
``exposedAttributes``. These are the attributes returned when the
element itself is requested. Our fictuous employees tell people their
names and are quite proud of their titles, but they're shy when it
comes to their salary.

Two sample employees are created and added to the collection, so
there's some data to play with when you try this code out.

Finally, it builds a resource from the collection, which allows it to
be served. Resources are the things that Twisted serves -- they're
roughly equivalent to the concept of a web page or a view. Twisted
formally specifies what a resource *is* in an interface called
``IResource``. Although the collection isn't a resource itself, it can
be turned into one, in a process called "adaptation". That wraps the
collection with an object (called the adapter) which behaves like a
resource. That allows for a clean separation of concerns: being a
collection on one side, and serving that collection on the other.

Both Collections and Elements are adaptable to resources. This means
they're easy to integrate with existing Twisted Web object
hierarchies.

Trying it out
=============

.. testsetup::

   import json
   from tutorial.util import buildPath, Example

You can access the entire collection by sending an HTTP GET request to
the root resource. txYoga uses JSON as the default serialization
format. The examples use the ``json`` and ``httplib`` [#whyhttplib]_
modules from the standard library.

In the interest of readability, the examples use some helpers to make
requests. These will build the appropriate URL and make the HTTP
request. JSON decoding is done manually, so the response headers can
still be verified. If you want to use these yourself, they are
available in ``doc/tutorial/util.py``.


.. literalinclude:: util.py
   :language: python


The ``buildPath`` function creates a URL path, roughly as you'd
expect:

.. doctest::

   >>> buildPath("test.rpy")
   '/test.rpy'
   >>> buildPath("test.rpy", "lvh", "minions")
   '/test.rpy/lvh/minions'

Create an Example object for this tutorial example (``accessing``):

.. doctest::

   >>> x = Example("accessing")

Accessing the collection
------------------------

.. doctest::

   >>> res = x.get()
   >>> json.load(res)
   {u'prev': None, u'results': [{u'name': u'lvh'}, {u'name': u'asook'}], u'next': None}

The important key here is ``results``. As you can see, has two
entries, one for every employee. Each entry is a dictionary,
containing the name of that employee. This is because
``Company.exposedElementAttributes`` only has ``name`` in it.

The two remaining keys, ``prev`` and ``next``, are there for
supporting pagination. In this case, they're both ``None``, indicating
that there is neither a previous nor a next page. A later tutorial
example will demonstrate how paginating collections works.

txYoga is being a good HTTP citizen behind the scenes, telling you the
date, the web server serving the request, and content length and type
behind the scenes.

.. doctest::

   >>> headers = res.getheaders()
   >>> headerKeys = [k for k, v in headers]
   >>> expectedKeys = ["date", "content-type", "content-length", "server"]
   >>> assert all(k in headerKeys for k in expectedKeys)

txYoga will never return responses with missing content types. A later
tutorial example on content type support in txYoga will elaborate on this.

.. doctest::

   >>> next(v for k, v in headers if k == "content-type")
   'application/json'

Admittedly, it really is Twisted Web telling you it's serving the
request and the time it served it, not txYoga, but it's still nice:

.. doctest::

   >>> serverName = next(v for k, v in headers if k == "server")
   >>> assert "TwistedWeb" in serverName

Accessing an element
--------------------

Let's look at this ``lvh`` employee from up close next.

.. doctest::

   >>> res = x.get("lvh")
   >>> json.load(res)
   {u'name': u'lvh', u'title': u'CEO'}

As expected, you get a dictionary back with the ``name`` and ``title``
attributes of the employee, because those are the keys in
``Employee.exposedAttributes``.

Although ``exposedElementAttributes`` and ``exposedAttributes`` are
typically defined on the class they are looked up on the instance for
each object. You could have a particular company that does expose the
titles of its employees when you query it, or a particular employee
that will divulge his salary.

As before, txYoga will serve the content type correctly:

.. doctest::

   >>> next(v for k, v in res.getheaders() if k == "content-type")
   'application/json'

Review
======

In this example, we've:

   1. shown what basic txYoga code looks like
   2. shown how the tutorial example helpers work
   3. accessed collections and their elements over HTTP

.. [#whyhttplib] The examples use ``httplib`` and not ``urllib`` or
  ``urllib2``, because it's less of an abstraction over HTTP. It
  supports for HTTP PUT and DELETE, which are obviously
  important. Although ``urllib2`` can be hacked at so that it does
  support those verbs, it's not very pretty. ``urllib`` itself is
  still used because it provides ``quote``.
