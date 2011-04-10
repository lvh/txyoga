"""
Generic utilities for testing txYoga.
"""
from functools import partial

from twisted.web import http_headers
from twisted.web.resource import IResource

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
