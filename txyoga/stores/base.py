# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Tools for building stores.
"""
class StoreDescriptorMixin(object):
    """
    A mixin for stores to implement the store descriptor behavior.
    """
    def __get__(self, collection, collectionClass):
        if collection is not None:
            return _CollectionStore(self, collection)
        else:
            return self



class _CollectionStore(object):
    """
    A store partially applied with a collection.
    """
    def __init__(self, store, collection):
        self._store = store
        self._collection = collection


    def __getattr__(self, name):
        method = getattr(self.store, name)
        return functools.partial(method, collection=self._collection)


    def __repr__(self):
        template = "<{0.__class__.__name__} ({0._store}, {0._collection})>"
        return template.format(self)