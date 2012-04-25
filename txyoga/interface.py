# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Interfaces for producing REST APIs for objects.
"""
from zope.interface import Attribute, Interface


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


    def get(identifier):
        """
        Get the element with this identifier from the collection.

        Returns a ``Deferred`` that fires with the requested element.
        """


    def query(**kwargs):
        """
        Gets the elements in the collection that match a query.

        Returns a ``Deferred`` that fires with the requested elements.
        """


    def add(element):
        """
        Adds the element to the collection.

        Returns a ``Deferred`` that fires when the element has been added.
        """


    def remove(identifier):
        """
        Remove the element with a given identifier from the collection.

        Returns a ``Deferred`` that fires when the element has been removed.
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

        The value of this attribute must be unique in the collection.
        """)


    def toState(attrs=ALL):
        """
        Export the state of this object.

        Returns a ``Deferred`` that will fire with the state of this object.
        """
    

    def fromState(state):
        """
        Creates a new object from the given state.

        Returns a `Deferred` that will fire with the new element.
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
