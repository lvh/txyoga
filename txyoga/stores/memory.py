# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
In-memory store.
"""
import collections
from zope import interface as zi

from twisted.internet import defer

from txyoga.stores import interface as istore, exceptions


class MemoryStore(object):
    """
    An in-memory store.
    """
    zi.implements(istore.IStore)

    def __init__(self):
        self._records = {}


    def get(self, collection, identifier):
        try:
            element = self._records[collection][identifier]
            return defer.succeed(element)
        except KeyError:
            return defer.fail(exceptions.MissingElementError(identifier))


    def query(self, collection, start=0, stop=None):
        elements = self._records[collection][start:stop]
        return defer.succeed(elements)


    def add(self, collection, element):
        try:
            record = self._records[collection]
        except KeyError:
            record = _CollectionRecord()
            self._records[collection] = record

        try:
            identifier = getattr(element, element.identifyingAttribute)
            record[identifier] = element
        except KeyError:
            return defer.fail(exceptions.DuplicateElementError(identifier))

        return defer.succeed(None)

 
    def remove(self, collection, identifier):
        try:
            record = self._records[collection]
        except KeyError:
            e = exceptions.UnknownCollectionError(collection, self)
            return defer.fail(e)

        try:
            del record[identifier]
        except KeyError:
            return defer.fail(exceptions.MissingElementError(identifier))
        else:
            return defer.succeed(None)



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
            raise KeyError("duplicate key {}".format(key))

        self._mapping[key] = value
        self._elements.append(value)


    def __delitem__(self, key):
        element = self._mapping.pop(key)
        self._elements.remove(element)
