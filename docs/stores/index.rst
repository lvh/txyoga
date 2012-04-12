========
 Stores
========

Stores are an abstraction layer for the tools used to store or persist
collections and elements.

By default, there is an in-memory store that is used for all objects
that don't specify any other kind of store.

Interface
=========

Note that all jar methods return a deferred. However, because we're
using an in-memory store, we know that the operations *actually* occur
synchronously. In order to make the doctests easier to read, we create
a function that swallows the deferred:

.. doctest::

    >>> def s(expr): pass

Normally, you would use something like ``gatherResults`` to wait for
all operations to be completed.

Let's say that we have a cookie jar with an associated store.

.. doctest::

    >>> from txyoga.stores import memory
    >>> store = memory.MemoryStore()
    >>> from txyoga.test import collections
    >>> class Jar(collections.Jar):
    ...     store = store
    >>> jar = Jar()
    >>> s(store.register(jar))

When you access a store on the collection class, you get that store:

.. doctest::

    >>> Jar.store is store
    True

When you access a store on a collection *instance*, you get that
store, partially applied with that collection instance:

    >>> jar.store is not store
    True
    >>> add = jar.store.add
    >>> add.func.im_self is store
    True
    >>> arg, = add.args
    >>> arg is jar
    True

This works analogously to methods being accessed on instances or on
the class.

Let's add some cookies to the jar.

.. doctest::

    >>> cookieNames = "sugar", "chocolate chip", "shortbread"
    >>> cookies = [collections.Cookie(name) for name in cookieNames]
    >>> for cookie in cookies:
    ...     s(jar.store.add(cookie))

Note that the elements will only be available immediately because the
in-memory store is synchronous. In general, stores might take a long
tiem to actually complete a transaction. This is why the ``add``
method returns a Deferred. So, normally, you would use something like
``twisted.internet.defer.gatherResults`` to wait for all the cookies
to be added.

