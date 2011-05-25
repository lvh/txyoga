================================
 Creating and deleting elements
================================

In computing, there is a common term called CRUD_: creating, reading
(accessing), updating and deleting. In the :doc:`previous example
<accessing>`, you learned how to retrieve collections and elements
over HTTP. In this example, we'll show how creating and deleting
elements in collections works.

.. _CRUD: http://en.wikipedia.org/wiki/Create,_read,_update_and_delete

Example code
============

The example code is very similar, but not identical to that in the
previous example.

First of all, there is the ``updatableAttributes`` attribute on the
element class. This is an iterable of the attribute names for which
updates are allowed. In this case, it's ``salary`` and ``title`` -- we
can give people new positions and give them raises, but not change
their names.

Then there is the ``elementClass`` attribute on the collection
class. By default, this class will be instantiated when new elements
are added.

Trying it out
=============

.. testsetup::

   import json
   from tutorial.util import Example

Like before, start by creating the helper object for this example:

.. doctest::

   >>> example = Example("crud")

Creating an element
-------------------

First, we'll hire a new employee in the company. In REST, there are
two usual ways of creating elements:

   1. If you just want to add an element to a Collection and you don't
   care what URL it will be available under, POST to the collection.
   2. If you want to make an element accessible at a particular path,
   PUT it there.

Just like everywhere else, when faced with doubt, txYoga refuses the
temptation to guess. In this case, when you provide data through POST
or PUT, specifying the encoding is mandatory.

.. doctest::

   >>> data = {"name": u"alice"}
   >>> headers = {"content-type": "application.json"}
   >>> response = example.put(json.dumps(data), headers, "alice")

As usual, we get the appropriate response:

.. doctest::

   >>> response.status, response.reason

Updating an element
-------------------

Now that the company's grown, lvh really deserves a title bump and a
raise. In REST, updates are typically done using a PUT request.

Deleting an element
-------------------

Next, we'll remove poor Asook from the workforce. As you might expect
from a REST toolkit, you do that with the DELETE verb, or, with our
helper abstraction layer, the ``delete`` method.

.. doctest::

   >>> response = example.delete("asook")

The server will respond with the appropriate response code:

.. doctest::

   >>> response.status, response.reason
   (204, 'No Content')

When you access the collection again, Asook is missing, as expected:

.. doctest::

   >>> employees = json.load(example.get())["results"]
   >>> assert u"asook" not in employees
