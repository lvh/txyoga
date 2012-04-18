# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Tests for basic class serialization and deserialization.
"""
from twisted.trial.unittest import TestCase

from txyoga import errors
from txyoga.base import Collection, Element
from txyoga.serializers import jsonEncode


class Screwdriver(Element):
    """
    A screwdriver.
    """
    exposedAttributes = "head", "size"
    identifyingAttribute = "size"

    def __init__(self, head, size):
        self.head = head
        self.size = size



class Toolbox(Collection):
    """
    A toolbox.
    """
    defaultElementClass = Screwdriver



class SerializationTest(TestCase):
    """
    Test that serializing to some state works.
    """
    def test_complete(self):
        """
        Test serialization of a screwdriver.
        """
        screwdriver = Screwdriver("philips", "m3")
        state = screwdriver.toState()
        self.assertEqual(state, {"head": "philips", "size": "m3"})


    def test_partial(self):
        """
        Test partial serialization of a screwdriver.
        """
        screwdriver = Screwdriver("philips", "m3")
        state = screwdriver.toState(["size"])
        self.assertEqual(state, {"size": "m3"})



class DeserializationTest(TestCase):
    """
    Test that deserializing from some state works.
    """
    def test_deserialize(self):
        """
        Deserialize a screwdriver.
        """
        state = {"head": "philips", "size": "m3"}
        screwdriver = Screwdriver.fromState(state)

        for attr, value in state.iteritems():
            self.assertEqual(getattr(screwdriver, attr), value)



class ElementCreationTest(TestCase):
    """
    Test the creation of new screwdrivers.
    """
    def test_createElement(self):
        """
        Creates a screwdriver from some state, and verify that it has
        correctly materialized.
        """
        toolbox = Toolbox()
        state = {"head": "philips", "size": "m3"}
        screwdriver = toolbox.createElementFromState(state)

        for attr, value in state.iteritems():
            self.assertEqual(getattr(screwdriver, attr), value)



class JSONEncoderTests(TestCase):
    """
    Test JSON encoding.
    """
    def test_raiseForUnserializableType(self):
        """
        When given an unserializable type, the serializer should raise
        TypeError instead of failing silently.
        """
        self.assertRaises(TypeError, jsonEncode, object())
