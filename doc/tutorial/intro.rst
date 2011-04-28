=======================
 Getting your feet wet
=======================

To introduce txYoga, we're going to start with a simple example of a
bunch of employees who work at a startup (because blogs with articles
are just cliché).

.. literalinclude:: 1.rpy
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

Let's test if all of that actually works.

.. testsetup::

   import json
   import urllib

You can access the entire collection by sending an HTTP GET request to
the root resource. txYoga uses JSON as the default serialization
format.

.. doctest::

   >>> json.load(urllib.urlopen("http://localhost:8080/1.rpy"))
   {u'prev': None, u'results': [{u'name': u'lvh'}, {u'name': u'asook'}], u'next': None}

The important key here is ``results``. As you can see, has two
entries, one for every employee. Each entry is a dictionary,
containing the name of that employee. This is because
``Company.exposedElementAttributes`` only has ``name`` in it.

The two remaining keys, ``prev`` and ``next``, are there for
supporting pagination. In this case, they're both ``None``, indicating
that there is neither a previous nor a next page.

Let's look at this ``lvh`` employee from up close next.

.. doctest::

   >>> json.load(urllib.urlopen("http://localhost:8080/1.rpy/lvh"))
   {u'name': u'lvh', u'title': u'CEO'}

As expected, you get a dictionary back with the ``name`` and ``title``
attributes of the employee, because those are the keys in
``Employee.exposedAttributes``.

Although ``exposedElementAttributes`` and ``exposedAttributes`` are
typically defined on the class they are looked up on the instance for
each object. You could have a particular company that does expose the
titles of its employees when you query it, or a particular employee
that will divulge his salary.
