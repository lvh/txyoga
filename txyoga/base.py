# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Base classes for objects that will be exposed through a REST API.
"""
import inspect
from functools import partial

from twisted.internet import defer
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
        originalState = state.copy()

        try:
            initArgs = {}
            for arg in inspect.getargspec(cls.__init__).args[1:]:
                initArgs[arg] = state.pop(arg)
        except KeyError:
            raise errors.ElementStateMissingAttributeError(originalState, arg)

        try:
            element = cls(**initArgs)
        except TypeError:
            raise errors.InvalidElementStateError(state)

        for remaining, value in state.iteritems():
            assert getattr(element, remaining) == value

        return element


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
                return defer.fail(UpdateError(currentValue=current))
            else: # Don't expose the current value by accident
                return defer.fail(UpdateError())
    
        for attr in toUpdate:
            setattr(self, attr, state[attr])

        return defer.succeed(None)



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


    def get(self, identifier):
        try:
            return defer.succeed(self._elementsByIdentifier[identifier])
        except KeyError:
            return defer.fail(errors.MissingElementError(identifier))


    def query(self, start, stop):
        return defer.succeed(self._elements[start:stop])


    def add(self, element):
        identifier = getattr(element, element.identifyingAttribute)

        if identifier in self._elementsByIdentifier:
            raise errors.DuplicateElementError(identifier)

        self._elementsByIdentifier[identifier] = element
        self._elements.append(element)

        return defer.succeed(element)


    def remove(self, identifier):
        try:
            element = self._elementsByIdentifier.pop(identifier)
            self._elements.remove(element)
            return defer.succeed(element)
        except KeyError:
            return defer.fail(errors.MissingElementError(identifier))
