# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Interfaces for producing REST APIs for objects.
"""
from zope.interface import Attribute, Interface


class IStore(Interface):
    """
    An interface to a data store.
    """
    def get(identifier):
        """
        Gets the element with the given identifier.

        Returns a ``Deferred`` that will fire with the requested element or
        will fail if the element could not be retrieved.
        """


    def query(start=0, stop=None):
        """
        Gets the elements that match the given query parameters.

        Returns a ``Deferred`` that will fire with the requested element or
        will fail if the elements could not be retrieved.
        """


    def add(element):
        """
        Adds the given element.

        Returns a ``Deferred`` that will fire when the element has been added
        to the store, or will fail if the element could not be added. Returns
        ``None`` if this store does not support confirmation.
        """


    def remove(identifier):
        """
        Remove the element with the given identifier.

        Returns a ``Deferred`` that will fire when the element has been
        removed to the store, or will fail if the element could not be added.
        Returns ``None`` if this store does not support confirmation.
        """



class ICollection(Interface):
    """
    A collection in a REST API.
    """
    exposedElementAttributes = Attribute(
        """
        The names of the attributes this collection exposes of its elements.
        """)


    def createElementFromState(state):
        """
        Creates an element from an element state.
        """



ALL = object()



class IElement(Interface):
    """
    An element in a REST API.
    """
    children = Attribute(
        """
        The names of the children this element exposes.
        """)


    identifyingAttribute = Attribute(
        """
        The attribtue used to define this element.

        Must be unique among all other elements in any collection.
        """)


    def toState(attrs=ALL):
        """
        Exports a serializable state of this object.
        """
    

    def fromState(state):
        """
        Creates a new object with the given state as the new internal state.
        """



class ISerializableError(Interface):
    """
    A serializable error.
    """
    responseCode = Attribute(
        """
        The HTTP response code for this error.
        """)


    message = Attribute(
        """
        A human-readable error message.
        """)


    details = Attribute(
        """
        Some error-specific details.
        """)
