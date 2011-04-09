# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Base classes for objects that will be exposed through a REST API.
"""
from zope.interface import implements

from twisted.web import http

from txyoga import interface, resource


class Element(object):
    implements(interface.IElement)

    children = ()
    exposedAttributes = ()
    identifyingAttribute = "name"
    updatableAttributes = ()

    name = "default"


    def toState(self, attrs=interface.ALL):
        """
        Returns the state of this object in a serializable form.
        """
        if attrs is interface.ALL:
            attrs = self.exposedAttributes

        state = {}
        for attr in attrs:
            state[attr] = self.getSerializableAttribute(attr)

        return state


    def getSerializableAttribute(self, name):
        """
        Returns an attribute in a serializable form.

        Override this method if you have attributes that aren't serializable.
        """
        return getattr(self, name)


    @classmethod
    def fromState(cls, state):
        """
        Constructs a new object from this state.
        """
        return cls(**state)


    def update(self, state):
        """
        Updates an instance with new state.

        @raise L{ForbiddenAttributeUpdateError}
        """
        if any(attr not in self.updatableAttributes for attr in state):
            requested, allowed = list(state), self.updatableAttributes
            raise ForbiddenAttributeUpdateError(requested, allowed)

        for attr, value in state.iteritems():
            setattr(self, attr, value)



class Collection(object):
    implements(interface.ICollection)

    defaultElementClass = Element
    exposedElementAttributes = ()

    pageSize = 10
    maxPageSize = 100


    def __init__(self):
        self._elements = []
        self._elementsByIdentifier = {}


    def createElementFromState(self, state):
        return self.defaultElementClass.fromState(state)


    def add(self, element):
        identifier = getattr(element, element.identifyingAttribute)

        if identifier in self._elementsByIdentifier:
            raise ValueError("duplicate element (%s)" % (identifier,))

        self._elementsByIdentifier[identifier] = element
        self._elements.append(element)


    def removeByIdentifier(self, identifier):
        element = self._elementsByIdentifier.pop(identifier)
        self._elements.remove(element)


    def __getitem__(self, sliceOrIdentifier):
        if isinstance(sliceOrIdentifier, slice):
            return self._elements[sliceOrIdentifier]

        return self._elementsByIdentifier[sliceOrIdentifier]



class ForbiddenAttributeUpdateError(resource.SerializableError):
    responseCode = http.FORBIDDEN


    def __init__(self, requestedAttributes, updatableAttributes):
        message = "attribute update not allowed, update aborted"
        details = {"updatableAttributes": updatableAttributes,
                   "requestedAttributes": requestedAttributes}
        resource.SerializableError.__init__(self, message, details)
