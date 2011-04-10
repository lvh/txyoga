# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Basic tests for REST functionality.
"""
from math import ceil
from urlparse import urlsplit, parse_qsl

from twisted.trial.unittest import TestCase
from twisted.web.resource import IResource
from twisted.web import http, http_headers

from txyoga import base
from txyoga.interface import ICollection
from txyoga.serializers import json
from txyoga.test import util, collections


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

        collection.add(element)
        self.assertRaises(ValueError, collection.add, element)



class _BaseUnpaginatedCollectionTest(util._BaseCollectionTest):
    def test_getElements_none(self):
        """
        Tests that an empty collection reports no elements.
        """
        self.getElements()
        results = self.responseContent["results"]
        self.assertEqual(len(results), 0)


    def test_getElements_many(self):
        """
        Test on a collection with more than one element, but not enough of
        them to incur the wrath of the pagination monster.
        """
        self.addElements()
        self.getElements()
        results = self.responseContent["results"]
        self.assertEqual(len(results), len(self.elementArgs))


    def test_getElements_variable(self):
        """
        Test on a collection with varying content.

        This effectively tests if the resource correctly gets the data from
        the collection when the request is made, not at creation.
        """
        oldResource = self.resource

        self.getElements()
        results = self.responseContent["results"]
        self.assertEqual(len(results), 0)

        self.assertEqual(self.resource, oldResource)

        self.addElements()
        self.getElements()
        results = self.responseContent["results"]
        self.assertEqual(len(results), len(self.elementArgs))

        self.assertEqual(self.resource, oldResource)



class Jar(base.Collection):
    """
    A cookie jar.
    """



class Cookie(base.Element):
    """
    A cookie, typically contained in a jar.
    """
    def __init__(self, name):
        self.name = name



class SimpleCollectionTest(_BaseUnpaginatedCollectionTest, TestCase):
    collectionClass = Jar
    elementClass = Cookie
    elementArgs = [("chocolateChip",),
                   ("butter",),
                   ("gingerbread",)]



class PartlyExposingCollectionTest(collections._PartlyExposingCollectionMixin,
                                   _BaseUnpaginatedCollectionTest, TestCase):
    """
    Test that exposing some attributes works.
    """
    def test_exposedAttributes(self):
        """
        Test that all of the exposed attributes (and *only* the exposed
        attributes) of an element are exposed when querying the collection.

        When the element is queried directly, it correctly exposes all of its
        attributes.
        """
        self.addElements()
        self.getElements()
        results = self.responseContent["results"]
        for result in results:
            for attribute in self.elementClass.exposedAttributes:
                if attribute in self.collectionClass.exposedElementAttributes:
                    self.assertIn(attribute, result)
                else:
                    self.assertNotIn(attribute, result)

            self.getElement(result["name"])

            for attribute in self.elementClass.exposedAttributes:
                self.assertIn(attribute, self.responseContent)



class PaginatedCollectionTest(collections._PaginatedCollectionMixin, TestCase):
    """
    Tests for paginated collections.
    """
    def test_firstPage(self):
        """
        Test the first page of a collection.

        It should be of the correct size, not have a link to a previous page
        (since there is none), and have a link to the next page (since there
        is one).
        """
        self.addElements()
        self.getElements()

        self.assertEqual(len(self.responseContent["results"]),
                         self.collectionClass.pageSize)

        self.assertEqual(self.responseContent["prev"], None)
        self.assertNotEqual(self.responseContent["next"], None)


    def test_followPages(self):
        """
        Tests that the entire collection can be accessed by walking down all
        the pages sequentially.
        """
        self.addElements()
        elementsPerPage = []

        pageSize = self.collectionClass.pageSize
        pages = int(ceil(float(len(self.elementArgs))/pageSize))

        def hashable(d):
            """
            A hashable version of an element.

            Used to check if an element has been seen before or not.
            """
            return tuple(sorted(d.itervalues()))

        def isLast(index):
            """
            Checks if this is the index of the last page.
            """
            return index == pages - 1

        def nextPageArgs():
            """
            Gets the args used to get the next page
            """
            nextURL = self.responseContent["next"]
            _, _, _, qs, _ = urlsplit(nextURL)
            nextQuery = parse_qsl(qs)

            nextQueryKeys = [key for key, _ in nextQuery]
            for key in ("start", "stop"):
                self.assertEqual(nextQueryKeys.count(key), 1)

            return dict((k, [v]) for k, v in nextQuery)

        args = {}

        for index in xrange(pages):
            seenElements = set()
            elementsPerPage.append(seenElements)

            self.getElements(args)
            newElements = map(hashable, self.responseContent["results"])

            for element in newElements:
                # Test that the element is not duplicated in this page
                self.assertNotIn(element, seenElements)
                seenElements.add(element)

                # Test that the element is not duplicated in a previous page
                for previousPageElements in elementsPerPage[:-1]:
                    self.assertNotIn(element, previousPageElements)

            if not isLast(index):
                args = nextPageArgs()

        self.assertIdentical(self.responseContent["next"], None)



class ElementUpdatingTests(collections._UpdatableCollectionMixin, TestCase):
    """
    Tests to verify if updating an element works as expected.
    """
    uselessUpdateBody = {"color": "green"}
    usefulUpdateBody = {"maximumOccupancy": 200}


    def setUp(self):
        collections._UpdatableCollectionMixin.setUp(self)
        self.addElements()
        self.headers = http_headers.Headers()
        self.body = self.uselessUpdateBody


    def _test_updateElement(self, expectedStatusCode=None):
        """
        Tries to change the color of a bikeshed.
        """
        name = self.elementArgs[0][0]
        self.getElement(name)
        expectedContent = self.responseContent

        encodedBody = json.dumps(self.body)
        self.updateElement(name, encodedBody, self.headers)

        expectFailure = expectedStatusCode is not None
        if expectFailure:
            # A failed PUT has a response body
            self._checkContentType("application/json")
            self._decodeResponse()
            self._checkBadRequest(expectedStatusCode)
        else:
            # A successful PUT does not have a response body
            self._checkContentType(None)
            expectedContent["color"] = self.body["color"]

        self.getElement(name)
        self.assertEqual(self.responseContent, expectedContent)


    def test_updateElement(self):
        """
        Test that updating an element works.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self._test_updateElement()


    def test_updateElement_missingContentType(self):
        """
        Test that trying to update an element when not specifying the content
        type of the update content fails.
        """
        self._test_updateElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_updateElement_badContentType(self):
        """
        Test that trying to update an element when specifying a bogus content
        type of the update content fails.
        """
        self.headers.setRawHeaders("Content-Type", ["ZALGO/ZALGO"])
        self._test_updateElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_updateElement_nonUpdatableAttribute(self):
        """
        Tests that updating an attribute which is not allowed to be updated
        responds that that operation is forbidden.

        Try to make the bikeshed twice as large, which won't work because that
        would be a useful change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = self.usefulUpdateBody
        self._test_updateElement(http.FORBIDDEN)


    def test_updateElement_partiallyUpdatableAttributes(self):
        """
        Tests that updates are atomic; when part of an update is not allowed,
        the entire update does not happen.

        Try to make the bikeshed twice as large and change its color.  Both
        will fail, since the useful operation blocks the entire change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = dict(self.usefulUpdateBody)
        self.body.update(self.uselessUpdateBody)
        self._test_updateElement(http.FORBIDDEN)



class ElementDeletionTests(collections._UpdatableCollectionMixin, TestCase):
    # XXX: does this need to be _UpdatableCollectionMixin?
    """
    Tests deleting elements from a collection.
    """
    def setUp(self):
        collections._UpdatableCollectionMixin.setUp(self)
        self.addElements()


    def _checkSuccessfulDeletion(self):
        self.assertEqual(self.request.code, http.NO_CONTENT)
        self._checkContentType(None)


    def _checkFailedDeletion(self):
        # A failed DELETE has a response body, check it
        self._checkContentType("application/json")
        self._decodeResponse()
        self._checkBadRequest(http.NOT_FOUND)


    def test_deleteElement(self):
        """
        Delete an element, check response.
        """
        name = self.elementArgs[0][0]
        self.deleteElement(name)
        self._checkSuccessfulDeletion()


    def test_deleteElement_missing(self):
        """
        Delete an element that doesn't exist, check response.
        """
        self.deleteElement("bogus")
        self._checkFailedDeletion()


    def test_deleteElement_twice(self):
        """
        Delete an element, check response, delete it again, check response.
        """
        name = self.elementArgs[0][0]
        self.deleteElement(name)
        self._checkSuccessfulDeletion()
        self.deleteElement(name)
        self._checkFailedDeletion()
