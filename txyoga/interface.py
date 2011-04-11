# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
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


    def add(element):
        """
        Adds an element to this collection.
        """
    
    
    def __getitem__(sliceOrIdentifier):
        """
        Gets a particular element by identifier or a slice of elements.
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

        Must be unique among all elements in a particular collection. Doesn't
        have to be exposed as well, but it probably doesn't make sense to do
        that.
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
