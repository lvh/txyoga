"""
Tests for basic class serialization and deserialization.
"""
from twisted.trial.unittest import TestCase

from txyoga.base import Collection, Element


class Screwdriver(Element):
    exposedAttributes = "head", "size"
    identifyingAttribute = "size"


    def __init__(self, head, size):
        self.head = head
        self.size = size



class Toolbox(Collection):
    defaultElementClass = Screwdriver



class SerializationTest(TestCase):
    def test_serialization_complete(self):
        screwdriver = Screwdriver("philips", "m3")
        state = screwdriver.toState()
        self.assertEqual(state, {"head": "philips", "size": "m3"})


    def test_serialization_partial(self):
        screwdriver = Screwdriver("philips", "m3")
        state = screwdriver.toState(["size"])
        self.assertEqual(state, {"size": "m3"})



class DeserializationTest(TestCase):
    def test_deserialization(self):
        state = {"head": "philips", "size": "m3"}
        screwdriver = Screwdriver.fromState(state)

        for attr, value in state.iteritems():
            self.assertEqual(getattr(screwdriver, attr), value)



class ElementCreationTest(TestCase):
    def test_createElement(self):
        toolbox = Toolbox()
        state = {"head": "philips", "size": "m3"}
        screwdriver = toolbox.createElementFromState(state)

        for attr, value in state.iteritems():
            self.assertEqual(getattr(screwdriver, attr), value)


        toolbox.add(screwdriver)
        self.assertEqual(toolbox[screwdriver.size], screwdriver)
        self.assertRaises(ValueError, toolbox.add, screwdriver)
