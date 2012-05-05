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

.. literalinclude:: crud.rpy
   :language: python

The example code is very similar, but not identical to that in the
previous example.

First of all, there is the ``updatableAttributes`` attribute on the
element class. This is an iterable of the attribute names for which
updates are allowed. In this case, it's ``salary`` and ``title`` -- we
can give people new positions and give them raises, but not change
their names.

Then there is the ``elementClass`` attribute on the collection
class. By default, this class will be instantiated when new elements
are added. In this case, new elements will be instances of the
``Employee`` class.

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

Just like everywhere else, when faced with doubt, txyoga refuses the
temptation to guess. In this case, when you provide data through POST
or PUT, specifying the encoding is mandatory.

.. doctest::

   >>> data = {"name": u"alice", "salary": 100, "title": "engineer"}
   >>> headers = {"content-type": "application/json"}
   >>> response = example.put(json.dumps(data), headers, "alice")
   
As usual, we get the appropriate response:

.. doctest::

   >>> response.status, response.reason
   (201, 'Created')

If accepted but not yet created, a txyoga server may optionally return
202 (Accepted).

Updating an element
-------------------

The company's success has really gotten to lvh's head. He's not happy
unless we give him a ridiculous new title.

To do that, we update his record. In REST, updates are typically done
using a PUT request.

.. doctest::

   >>> def getTitle(employee="lvh"):
   ...     response = example.get(employee)
   ...     return json.load(response)["title"]
   >>> assert getTitle() == u'CEO'
   >>> headers = {"content-type": "application/json"}
   >>> data = {"title": u"Supreme Commander"}
   >>> response = example.put(json.dumps(data), headers, "lvh")
   >>> response.status, response.reason
   (200, 'OK')
   >>> assert getTitle() == u'Supreme Commander'

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
