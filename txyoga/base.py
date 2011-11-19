# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Base classes for objects that will be exposed through a REST API.
"""
from functools import partial

from zope.interface import implements

from txyoga import errors, interface


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

        return dict((a, self.getSerializableAttribute(a)) for a in attrs)


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
        state = dict((str(k), v) for (k, v) in state.items())
        return cls(**state)


    def update(self, state):
        """
        Updates an instance with new state.

        Raises ``AttributeValueUpdateError`` when the state contains
        an attribute which isn't allowed to be updated and the
        matching attribute is not equal to the current value,
        i.e. you're trying to update a value that isn't allowed to be
        updated.
        """
        toUpdate = set()
        for attr in state:
            if attr in self.updatableAttributes:
                toUpdate.add(attr)
                continue

            current, new = getattr(self, attr), state[attr]
            if current == new:
                continue

            UpdateError = partial(errors.AttributeValueUpdateError,
                                  attribute=attr, newValue=new)
            if attr in self.exposedAttributes:
                raise UpdateError(currentValue=current)
            else: # Don't expose the current value by accident
                raise UpdateError()
    
        for attr in toUpdate:
            setattr(self, attr, state[attr])



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
