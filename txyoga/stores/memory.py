# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
In-memory store.
"""
import collections
import functools
from zope import interface as zi

from twisted.internet import defer

from txyoga.stores import base, exceptions, interface as istore


def _synchronous(f):
    @functools.wraps(f)
    def decorated(*a, **kw):
        try:
            return defer.succeed(f(*a, **kw))
        except Exception as e:
            return defer.fail(e)

    return decorated



class MemoryStore(base.StoreDescriptorMixin):
    """
    An in-memory store.
    """
    zi.implements(istore.IStore)

    def __init__(self):
        self._records = {}


    @_synchronous
    def register(self, collection):
        if collection not in self._records:
            self._records[collection] = _CollectionRecord()
        else:
            raise RuntimeError("duplicate registration TODO: REMOVE")


    def _getRecord(self, collection):
        try:
            return self._records[collection]
        except KeyError:
            raise exceptions.UnknownCollectionError(collection, self)


    @_synchronous
    def get(self, collection, identifier):
        try:
            return self._getRecord(collection)[identifier]
        except KeyError:
            raise exceptions.MissingElementError(identifier)


    @_synchronous
    def query(self, collection, start=0, stop=None):
        return self._getRecord(collection)[start:stop]


    @_synchronous
    def add(self, collection, element):
        record = self._getRecord(collection)
        identifier = getattr(element, element.identifyingAttribute)

        try:
            record[identifier] = element
        except KeyError:
            raise exceptions.DuplicateElementError(identifier)

        return None

 
    @_synchronous
    def remove(self, collection, identifier):
        try:
            del self._getRecord(collection)[identifier]
        except KeyError:
            raise exceptions.MissingElementError(identifier)



class _CollectionRecord(object):
    """
    An in-memory record for a single collection.
    """
    def __init__(self):
        self._elements = []
        self._mapping = {}


    def __contains__(self, key):
        return key in self._mapping


    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._elements[key]
        else:
            return self._mapping[key]


    def __setitem__(self, key, value):
        if key in self._mapping:
            raise KeyError("duplicate key {0}".format(key))

        self._mapping[key] = value
        self._elements.append(value)


    def __delitem__(self, key):
        element = self._mapping.pop(key)
        self._elements.remove(element)
