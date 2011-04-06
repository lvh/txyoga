"""
Tests for the REST API tools.
"""
from functools import partial
from math import ceil
from urlparse import urlsplit, parse_qsl

from twisted.trial.unittest import TestCase
from twisted.web.resource import IResource
from twisted.web import http, http_headers

from txyoga import base, resource
from txyoga.interface import ICollection, IElement
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
    Tests that Collections produce results with roughly the right data.
    """
    def test_adaptation(self):
        """
        Test that the Collection class can be adapted to an IResource.
        """
        collection = base.Collection()
        self.assertTrue(ICollection.providedBy(collection))
        self.assertTrue(IResource.providedBy(IResource(collection)))


    def test_uniqueElements(self):
        collection = base.Collection()
        element = base.Element()
        element.name = "Unobtainium"

        collection.add(element)
        self.assertRaises(ValueError, collection.add, element)



_FakePUTRequest = partial(_FakeRequest, method="PUT")
_FakeDELETERequest = partial(_FakeRequest, method="DELETE")



class _BaseCollectionTest(object):
    def setUp(self):
        self.collection = self.collectionClass()
        self.resource = IResource(self.collection)


    def addElements(self, elements=None):
        if elements is None:
            elements = [self.elementClass(*a) for a in self.elementArgs]

        for e in elements:
            self.collection.add(e)


    def _makeRequest(self, resource, request):
        self.request = request
        self.response = resource.render(request)


    def _decodeResponse(self):
        self.responseContent = json.loads(self.response)


    def _checkContentType(self, expectedContentType="application/json"):
        headers = self.request.responseHeaders.getRawHeaders("Content-Type")

        if expectedContentType is None:
            self.assertEqual(headers, None)
        else:
            self.assertEqual(headers, [expectedContentType])


    def _checkBadRequest(self, expectedCode):
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
        Tries to update an element.

        For a successful update, the headers should contain a Content-Type.
        """
        request = _FakePUTRequest(body=body, requestHeaders=headers)
        elementResource = self.resource.getChild(name, request)
        self._makeRequest(elementResource, request)


    def deleteElement(self, name):
        """
        Tries to delete an element.
        """
        request = _FakeDELETERequest()
        elementResource = self.resource.getChild(name, request)
        self._makeRequest(elementResource, request)



class _BaseUnpaginatedCollectionTest(_BaseCollectionTest):
    def test_getElements_none(self):
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
    maxPageSize= 5



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
    def test_firstPage(self):
        self.addElements()
        self.getElements()

        self.assertEqual(len(self.responseContent["results"]),
                         self.collectionClass.pageSize)

        self.assertEqual(self.responseContent["prev"], None)
        self.assertNotEqual(self.responseContent["next"], None)


    def test_followPages(self):
        self.addElements()
        elementsPerPage = []

        pageSize = self.collectionClass.pageSize
        pages = int(ceil(float(len(self.elementArgs))/pageSize))

        def hashable(d):
            return tuple(sorted(d.itervalues()))

        def isLast(index):
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
    A project that consists of a bunch of bikesheds.
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
    collectionClass = SoftwareProject
    elementClass = Bikeshed
    elementArgs = [("north", "red"),
                   ("east", "blue"),
                   ("south", "green"),
                   ("west", "yellow")]



class ElementUpdateTestCase(_BikeshedTest, TestCase):
    uselessUpdateBody = {"color": "green"}
    usefulUpdateBody = {"maximumOccupancy": 200}


    def setUp(self):
        _BikeshedTest.setUp(self)
        self.addElements()
        self.headers = http_headers.Headers()
        self.body = self.uselessUpdateBody


    def _test_updateElement(self, expectedStatusCode=None):
        """
        I am extremely important and must change the color of the very first
        bikeshed I can find.
        """
        name = self.elementArgs[0][0]
        self.getElement(name)
        expectedContent = self.responseContent

        encodedBody = json.dumps(self.body)
        self.updateElement(name, encodedBody, self.headers)

        expectFailure = expectedStatusCode is not None
        if expectFailure:
            # An failed PUT has a response body
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
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self._test_updateElement()


    def test_updateElement_missingContentType(self):
        self._test_updateElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_updateElement_badContentType(self):
        self.headers.setRawHeaders("Content-Type", ["ZALGO/ZALGO"])
        self._test_updateElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_updateElement_nonUpdatableAttribute(self):
        """
        I will try to make the bikeshed twice as large, which will fail since
        it is a useful change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = self.usefulUpdateBody
        self._test_updateElement(http.FORBIDDEN)


    def test_updateElement_partiallyUpdatableAttributes(self):
        """
        I will try to make the bikeshed twice as large and change its color.
        Both will fail, since the useful operation blocks the entire change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = dict(self.usefulUpdateBody)
        self.body.update(self.uselessUpdateBody)
        self._test_updateElement(http.FORBIDDEN)



class ElementDeletionTestCase(_BikeshedTest, TestCase):
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



class BadRequestTest(_BaseFailingRequestTest, TestCase):
    def test_multipleStarts(self):
        self._test_badCollectionRequest({"start": [0, 1]})


    def test_multipleStops(self):
        self._test_badCollectionRequest({"stop": [0, 1]})


    def test_negativePageSize(self):
        self._test_badCollectionRequest({"start": [0], "stop": [-1]})


    def test_pageTooBig(self):
        stop = self.collectionClass.maxPageSize + 1
        self._test_badCollectionRequest({"start": [0], "stop": [stop]})


    def test_startNotInteger(self):
        self._test_badCollectionRequest({"start": ["ZALGO"]})


    def test_stopNotInteger(self):
        self._test_badCollectionRequest({"stop": ["ZALGO"]})


    def test_bothNotInteger(self):
        self._test_badCollectionRequest({"start": ["ZALGO"], "stop": ["ZALGO"]})


    def test_badAcceptHeader(self):
        headers = http_headers.Headers()
        headers.setRawHeaders("Accept", ["text/bogus"])
        self._test_badCollectionRequest(None, headers, http.NOT_ACCEPTABLE)



class BadElementRequestTests(_BaseFailingRequestTest, TestCase):
    def test_missingElement(self):
        self._test_badElementRequest("bogus", None, None, http.NOT_FOUND)


    def test_missingElement_bogusAcceptHeader(self):
        headers = http_headers.Headers()
        headers.setRawHeaders("Accept", ["text/bogus"])
        self._test_badElementRequest("bogus", None, headers, http.NOT_FOUND)


    def test_getElement_bogusAcceptHeader(self):
        headers = http_headers.Headers()
        headers.setRawHeaders("Accept", ["text/bogus"])
        name, _, _ = self.elementArgs[0]
        self._test_badElementRequest(name, None, headers, http.NOT_ACCEPTABLE)



class JSONEncoderTest(TestCase):
    def test_raiseForUnserializableType(self):
        """
        When given an unserializable type, the serializer should raise
        TypeError instead of failing silently.
        """
        # Assumes TestCases aren't JSON serializable. Sounds reasonable?
        self.assertRaises(TypeError, resource.jsonEncode, self)
