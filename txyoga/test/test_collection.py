# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Test basic collection functionality.
"""
from twisted.internet import defer
from twisted.trial.unittest import TestCase
from twisted.web.resource import IResource

from txyoga import base, errors
from txyoga.interface import ICollection
from txyoga.test import collections


class CollectionTest(TestCase):
    """
    Test that Collections produce results with roughly the right data.
    """
    def test_adaptation(self):
        """
        Test that the Collection class can be adapted to an IResource.
        """
        collection = base.Collection()
        self.assertTrue(ICollection.providedBy(collection))
        self.assertTrue(IResource.providedBy(IResource(collection)))


    def test_uniqueElements(self):
        """
        Test that adding the same element to a collection more than once
        results in an error.
        """
        collection = base.Collection()
        element = base.Element()
        element.name = "Unobtainium"

        def add():
            collection.add(element)

        add()
        self.assertRaises(errors.DuplicateElementError, add)



class ElementChildTest(collections.ElementChildMixin, TestCase):
    """
    Test accessing children of elements.
    """
    def test_child(self):
        """
        Tests that a child can be accessed.
        """
        self.addElements()
        d = self.getElementChild("oceania", "ministries")
        d.addCallback(self._verifyChild)
        return d


    def _verifyChild(self, _):
        results = self.responseContent["results"]
        expectedResults = [{"name": name} for name in collections.ministryNames]
        self.assertEqual(results, expectedResults)



class UnpaginatedCollectionTest(collections.SimpleCollectionMixin, TestCase):
    """
    Test some generic invariants for collections small enough to fit
    in a single page.
    """
    def _verifyElementCount(self, expected):
        results = self.responseContent["results"]
        self.assertEqual(len(results), expected)

        self._checkPaginationLinks()
        

    def _verifyEmpty(self, _):
        self._verifyElementCount(0)


    def _verifyFull(self, _):
        self._verifyElementCount(len(self.elementArgs))


    def _checkPaginationLinks(self):
        """
        Verify that the response doesn't have a previous or a next page.
        """
        for link in ["next", "prev"]:
            self.assertIdentical(self.responseContent[link], None)


    def test_getEmptyCollection(self):
        """
        Tests that an empty collection reports no elements.
        """
        return self.getElements().addCallback(self._verifyEmpty)


    def test_getFullCollection(self):
        """
        Test on a collection with more than one element, but not enough of
        them to incur the wrath of the pagination monster.
        """
        self.addElements()
        return self.getElements().addCallback(self._verifyFull)


    def test_getVariableCollection(self):
        """
        Test on a collection with varying content.

        This effectively tests if the resource correctly gets the data from
        the collection when the request is made, not when it is created.
        """
        oldResource = self.resource

        def _verifySameResource(_):
            self.assertEqual(self.resource, oldResource)

        d = self.test_getEmptyCollection()
        d.addCallback(_verifySameResource)
        d.addCallback(lambda _: self.test_getFullCollection())
        d.addCallback(_verifySameResource)

        return d



class PartialExposureTest(collections.PartialExposureMixin, TestCase):
    """
    Test that exposing some, but not all, attributes works.
    """
    def test_exposedAttributes(self):
        """
        Test that all of the exposed attributes (and *only* the exposed
        attributes) of an element are exposed when querying the collection.

        When the element is queried directly, it correctly exposes all of its
        attributes.
        """
        self.addElements()
        d = self.getElements()
        d.addCallback(self._verifyExposedElementAttributes)
        d.addCallback(self._verifyExposedAttributes)
        return d


    def _verifyExposedElementAttributes(self, _):
        results = self.responseContent["results"]
        for result in results:
            for attribute in self.elementClass.exposedAttributes:
                if attribute in self.collectionClass.exposedElementAttributes:
                    self.assertIn(attribute, result)
                else:
                    self.assertNotIn(attribute, result)


    def _verifyExposedAttributes(self, _):
        # Yes, this has to be synchronous (one by one), because
        # getElement tacks a lot of ugly state on to the test case. It
        # really should return a nice (deferred) response object...
        # See issue #33
        def verifyElementExposure(_):
            for attribute in self.elementClass.exposedAttributes:
                self.assertIn(attribute, self.responseContent)

        d = defer.Deferred()

        names = [r["name"] for r in self.responseContent["results"]]
        for name in names:
            d.addCallback(lambda _: self.getElement(name))
            d.addCallback(verifyElementExposure)

        d.callback(None)
        return d
