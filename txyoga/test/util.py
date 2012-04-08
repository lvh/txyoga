"""
Generic utilities for testing txyoga.
"""
from functools import partial
from StringIO import StringIO

from twisted.web import http, http_headers
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
            self.content = StringIO(body)
        else:
            self.content = StringIO('')

        self.prePathURL = lambda: prePathURL
        # we're always directly aimed at a resource and nobody is doing any
        # postpath-related stuff, so let's just pretend it's always emtpy...
        self.postpath = []

        self.code = http.OK

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



_FakeDELETERequest = partial(_FakeRequest, method="DELETE")
_FakePOSTRequest = partial(_FakeRequest, method="POST")
_FakePUTRequest = partial(_FakeRequest, method="PUT")



class _BaseCollectionTest(object):
    """
    A base class for tests of a collection.
    """
    def setUp(self):
        self.collection = self.collectionClass()
        self.resource = IResource(self.collection)


    def addElements(self):
        """
        Adds some elements to the collection.

        Creates the default elements specified by the ``elementClass`` and
        ``elementArgs`` class attributes.
        """
        for element in [self.elementClass(*a) for a in self.elementArgs]:
            self.collection.add(element)


    def _makeRequest(self, resource, request):
        """
        Makes a request to a particular resource.
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


    def _getResource(self, args=None, headers=None, path=()):
        """
        Generalized GET for a particular resource.
        """
        request = _FakeRequest(args=args, requestHeaders=headers)

        resource = self.resource
        for childName in path:
            resource = resource.getChildWithDefault(childName, request)

        self._makeRequest(resource, request)
        self._checkContentType()
        self._decodeResponse()


    def getElements(self, args=None, headers=None):
        """
        Gets a bunch of elements from a collection.
        """
        self._getResource(args, headers)


    def getElement(self, element, args=None, headers=None):
        """
        Gets a particular element from a collection.
        """
        self._getResource(args, headers, [element])


    def getElementChild(self, element, child, args=None, headers=None):
        """
        Gets a child of a particular element from a collection.
        """
        self._getResource(args, headers, [element, child])


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


    def createElement(self, name, body, headers=None, method="PUT"):
        """
        Create a new element.
        """
        if method == "PUT":
            self.updateElement(name, body, headers)
        elif method == "POST":
            request = _FakePOSTRequest(body=body, requestHeaders=headers)
            self._makeRequest(self.resource, request)
