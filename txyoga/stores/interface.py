# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Interfaces for stores.
"""
from zope import interface as zi


class IStore(zi.Interface):
    """
    An interface to a data store.
    """
    def get(collection, identifier):
        """
        Get the element with this identifier from the collection.

        Returns a ``Deferred`` that will fire with the requested element or
        will fail if the element could not be retrieved.
        """


    def query(collection, start=0, stop=None):
        """
        Gets the elements in the collection that match the query.

        Returns a ``Deferred`` that will fire with the requested elements or
        will fail if the elements could not be retrieved.
        """


    def add(collection, element):
        """
        Adds the element to the collection.

        Returns a ``Deferred`` that will fire when the element has been added
        to the store, or will fail if the element could not be added. Returns
        ``None`` if this store does not support confirmation.
        """


    def remove(collection, identifier):
        """
        Remove the element with a given identifier from the collection.

        Returns a ``Deferred`` that will fire when the element has been
        removed to the store, or will fail if the element could not be added.
        Returns ``None`` if this store does not support confirmation.
        """
