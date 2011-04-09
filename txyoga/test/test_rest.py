# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Basic tests for REST functionality.
"""
from functools import partial
from math import ceil
from urlparse import urlsplit, parse_qsl

from twisted.trial.unittest import TestCase
from twisted.web.resource import IResource
from twisted.web import http, http_headers

from txyoga import base, resource
from txyoga.interface import ICollection
from txyoga.serializers import json



BASE_URL = "http://localhost"



class _FakeRequest(object):
    """
    Mimics a twisted.web.server.Request, poorly.
    """
    def __init__(self, args=None, body=None, method="GET",
                 prePathURL=BASE_URL, requestHeaders=None):
        self.args = args if args is not None else {}

        if body is not None:
            self.body = body

        self.prePathURL = lambda: prePathURL

        # we're always directly aimed at a resource and nobody is doing any
        # postpath-related stuff, so let's just pretend it's always emtpy...
        self.postpath = []

        if requestHeaders is not None:
            self.requestHeaders = requestHeaders
        else:
            self.requestHeaders = http_headers.Headers()
        self.responseHeaders = http_headers.Headers()
        self.method = method


    def setResponseCode(self, code):
        self.code = code


    def getHeader(self, name):
        # TODO: twisted ticket for inconsistent terminology (name/key)
        value = self.requestHeaders.getRawHeaders(name)
        if value is not None:
            return value[-1]


    def setHeader(self, name, value):
        self.responseHeaders.setRawHeaders(name, [value])



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



_FakePUTRequest = partial(_FakeRequest, method="PUT")
_FakeDELETERequest = partial(_FakeRequest, method="DELETE")



class _BaseCollectionTest(object):
    """
    A base class for tests of a collection.
    """
    def setUp(self):
        self.collection = self.collectionClass()
        self.resource = IResource(self.collection)


    def addElements(self, elements=None):
        """
        Adds some element to the collection.

        If no elements are specified, create the default elements specified by
        the elementClass and elementArgs class attributes.
        """
        if elements is None:
            elements = [self.elementClass(*a) for a in self.elementArgs]

        for e in elements:
            self.collection.add(e)


    def _makeRequest(self, resource, request):
        """
        Gets the response to a request.
        """
        self.request = request
        self.response = resource.render(request)


    def _decodeResponse(self):
        """
        Tries to decode the body of a response.
        """
        self.responseContent = json.loads(self.response)


    def _checkContentType(self, expectedContentType="application/json"):
        """
        Verifies the content type of a response.

        If the type is ``None``, verifies that the header is not passed. This
        is intended for cases where an empty response body is expected.
        """
        headers = self.request.responseHeaders.getRawHeaders("Content-Type")

        if expectedContentType is None:
            self.assertEqual(headers, None)
        else:
            self.assertEqual(headers, [expectedContentType])


    def _checkBadRequest(self, expectedCode):
        """
        Tests that a failed request has a particular response code, and that
        the response content has an error message and some details in it.
        """
        self.assertEqual(self.request.code, expectedCode)
        self.assertIn("errorMessage", self.responseContent)
        self.assertIn("errorDetails", self.responseContent)


    def getElements(self, args=None, headers=None):
        """
        Gets a bunch of elements from a collection.
        """
        request = _FakeRequest(args=args, requestHeaders=headers)
        self._makeRequest(self.resource, request)
        self._checkContentType()
        self._decodeResponse()


    def getElement(self, name, args=None, headers=None):
        """
        Gets a particular element from a collection.
        """
        request = _FakeRequest(args=args, requestHeaders=headers)
        elementResource = self.resource.getChild(name, request)
        self._makeRequest(elementResource, request)
        self._checkContentType()
        self._decodeResponse()


    def updateElement(self, name, body, headers=None):
        """
        Update an element.

        For a successful update, the headers should contain a Content-Type.
        """
        request = _FakePUTRequest(body=body, requestHeaders=headers)
        elementResource = self.resource.getChild(name, request)
        self._makeRequest(elementResource, request)


    def deleteElement(self, name):
        """
        Delete an element.
        """
        request = _FakeDELETERequest()
        elementResource = self.resource.getChild(name, request)
        self._makeRequest(elementResource, request)



class _BaseUnpaginatedCollectionTest(_BaseCollectionTest):
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



class Zoo(base.Collection):
    """
    A zoo.
    """
    exposedElementAttributes = "name", "species"

    pageSize = 3
    maxPageSize = 5



class Animal(base.Element):
    """
    An animal in captivity.
    """
    exposedAttributes = "name", "species", "diet"

    def __init__(self, name, species, diet):
        self.name = name
        self.species = species
        self.diet = diet



class PartlyExposingCollectionTest(_BaseUnpaginatedCollectionTest, TestCase):
    collectionClass = Zoo
    elementClass = Animal
    elementArgs = [("Pumbaa", "warthog", "bugs"),
                   ("Simba", "lion", "warthogs"),
                   ("Timon", "meerkat", "bugs")]


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
            for attribute in Animal.exposedAttributes:
                if attribute in Zoo.exposedElementAttributes:
                    self.assertIn(attribute, result)
                else:
                    self.assertNotIn(attribute, result)

            self.getElement(result["name"])

            for attribute in Animal.exposedAttributes:
                self.assertIn(attribute, self.responseContent)



class _BasePaginatedCollectionTest(_BaseCollectionTest):
    collectionClass = Zoo
    elementClass = Animal
    elementArgs = [("Pumbaa", "warthog", "bugs"),
                   ("Simba", "lion", "warthogs"),
                   ("Timon", "meerkat", "bugs"),
                   ("Rafiki", "mandrill", "strange yellow fruit"),
                   ("Zazu", "hornbill", "nondescript berries"),
                   ("Shenzi", "hyena", "lion cubs"),
                   ("Banzai", "hyena", "lion cubs"),
                   ("Ed", "hyena", "whatever he can get, really")]



class PaginatedCollectionTest(_BasePaginatedCollectionTest, TestCase):
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
            Checks if this is the last index or not.
            """
            return index == pages - 1

        args = {}

        for index in xrange(pages):
            theseElements = set()
            elementsPerPage.append(theseElements)

            self.getElements(args)
            newElements = self.responseContent["results"]

            for element in newElements:
                element = hashable(element)
                self.assertNotIn(element, theseElements,
                    "duplicate element in page")
                theseElements.add(element)

                for previousElements in elementsPerPage[:-1]:
                    self.assertNotIn(element, previousElements,
                        "duplicate element in previous page")

                nextURL = self.responseContent["next"]
                if not isLast(index):
                    _, _, _, qs, _ = urlsplit(nextURL)
                    nextQuery = parse_qsl(qs)
                    nextQueryKeys = [key for key, _ in nextQuery]
                    for x in ("start", "stop"):
                        self.assertEqual(nextQueryKeys.count(x), 1,
                            "next page url has duplicate %s" % (x,))
                    args = dict((k, [v]) for k, v in nextQuery)
                else:
                    self.assertIdentical(self.responseContent["next"], None,
                        "last page links to nonexistent next page")



class SoftwareProject(base.Collection):
    """
    A software project that consists of a bunch of bikesheds.
    """



class Bikeshed(base.Element):
    """
    A bikeshed.
    """
    exposedAttributes = "name", "color", "maximumOccupancy"
    updatableAttributes = "color",

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.maximumOccupancy = 100



class _BikeshedTest(_BaseCollectionTest):
    """
    Tests that use bikesheds.
    """
    collectionClass = SoftwareProject
    elementClass = Bikeshed
    elementArgs = [("north", "red"),
                   ("east", "blue"),
                   ("south", "green"),
                   ("west", "yellow")]



class ElementUpdatingTests(_BikeshedTest, TestCase):
    """
    Tests to verify if updating an element works as expected.
    """
    uselessUpdateBody = {"color": "green"}
    usefulUpdateBody = {"maximumOccupancy": 200}


    def setUp(self):
        _BikeshedTest.setUp(self)
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



class ElementDeletionTests(_BikeshedTest, TestCase):
    """
    Tests deleting elements from a collection.
    """
    def setUp(self):
        _BikeshedTest.setUp(self)
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



class _BaseFailingRequestTest(_BasePaginatedCollectionTest):
    """
    Base class for classes that make failing requests.
    """
    def _test_badCollectionRequest(self, args=None, headers=None,
                         expectedCode=http.BAD_REQUEST):
        """
        A request for a collection that's expected to fail.
        """
        self.addElements()
        self.getElements(args, headers)
        self._checkBadRequest(expectedCode)


    def _test_badElementRequest(self, name, args=None, headers=None,
                                expectedCode=http.BAD_REQUEST):
        """
        A request for a particular element that's expected to fail.
        """
        self.addElements()
        self.getElement(name, args, headers)
        self._checkBadRequest(expectedCode)



class BadCollectionRequestTests(_BaseFailingRequestTest, TestCase):
    """
    Test the failures of bad requests to a collection.
    """
    def test_multipleStarts(self):
        """
        Providing multiple start values when requesting a page of a collection
        results in an error.
        """
        self._test_badCollectionRequest({"start": [0, 1]})


    def test_multipleStops(self):
        """
        Providing multiple stop values when requesting a page of a collection
        results in an error.
        """
        self._test_badCollectionRequest({"stop": [0, 1]})


    def test_negativePageSize(self):
        """
        A request with a stop value lower than the start value (supposedly
        requesting a negative number of elements) when requesting a page of a
        collection results in an error.
        """
        self._test_badCollectionRequest({"start": [0], "stop": [-1]})


    def test_pageTooBig(self):
        """
        Asking for a number of elements larger than the maximum page size when
        requesting a page of a collection results in an error.
        """
        stop = self.collectionClass.maxPageSize + 1
        self._test_badCollectionRequest({"start": [0], "stop": [stop]})


    def test_startNotInteger(self):
        """
        Providing a start value that isn't an integer when requesting a page
        of a collection results in an error.
        """
        self._test_badCollectionRequest({"start": ["ZALGO"]})


    def test_stopNotInteger(self):
        """
        Providing a stop value that isn't an integer when requesting a page
        of a collection results in an error.
        """
        self._test_badCollectionRequest({"stop": ["ZALGO"]})


    def test_startAndStopNotInteger(self):
        """
        Providing a start value and a stop value that aren't integers when
        requesting a page of a collection results in an error.
        """
        self._test_badCollectionRequest({"start": ["ZALGO"], "stop": ["ZALGO"]})


    def test_badAcceptHeader(self):
        """
        Providing a bogus Accept header when requesting a page results in an
        error.
        """
        headers = http_headers.Headers()
        headers.setRawHeaders("Accept", ["text/bogus"])
        self._test_badCollectionRequest(None, headers, http.NOT_ACCEPTABLE)



class BadElementRequestTests(_BaseFailingRequestTest, TestCase):
    """
    Test the failures of bad requests for a particular element.
    """
    def test_missingElement(self):
        """
        Requesting a missing element, results in a response that the element
        was not found (404).
        """
        self._test_badElementRequest("bogus", None, None, http.NOT_FOUND)


    def test_missingElement_bogusAcceptHeader(self):
        """
        Requesting a missing element results in a response that the element
        was not found, even with a bogus Accept header.
        """
        headers = http_headers.Headers()
        headers.setRawHeaders("Accept", ["text/bogus"])
        self._test_badElementRequest("bogus", None, headers, http.NOT_FOUND)


    def test_getElement_bogusAcceptHeader(self):
        """
        Requesting an element with a bogus Accept header results in a response
        that the resquest was not acceptable.
        """
        headers = http_headers.Headers()
        headers.setRawHeaders("Accept", ["text/bogus"])
        name, _, _ = self.elementArgs[0]
        self._test_badElementRequest(name, None, headers, http.NOT_ACCEPTABLE)



class JSONEncoderTests(TestCase):
    """
    Test JSON encoding.
    """
    def test_raiseForUnserializableType(self):
        """
        When given an unserializable type, the serializer should raise
        TypeError instead of failing silently.
        """
        # Assumes TestCases aren't JSON serializable. Sounds reasonable?
        self.assertRaises(TypeError, resource.jsonEncode, self)
