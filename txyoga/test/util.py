"""
Generic utilities for testing txyoga.
"""
from functools import partial
from StringIO import StringIO

from twisted.internet import defer
from twisted.web import http, http_headers, resource, server

from txyoga.serializers import json


BASE_URL = "http://localhost"
correctAcceptHeaders = http_headers.Headers()
correctAcceptHeaders.setRawHeaders("Accept", ["application/json"])



class _FakeRequest(object):
    """
    Mimics a twisted.web.server.Request, poorly.
    """
    def __init__(self, args=None, body="", method="GET",
                 prePathURL=BASE_URL, requestHeaders=None):
        self.args = args or {}

        self.content = StringIO(body)
        self._responseContent = StringIO()

        self.prePathURL = lambda: prePathURL
        # we're always directly aimed at a resource and nobody is doing any
        # postpath-related stuff, so let's just pretend it's always emtpy...
        self.postpath = []

        self.code = http.OK

        self.requestHeaders = requestHeaders or http_headers.Headers()
        self.responseHeaders = http_headers.Headers()
        self.method = method

        self._finished = False
        self._notifiers = []


    def write(self, part):
        self._responseContent.write(part)


    def finish(self):
        self._finished = True
        self._responseContent.seek(0, 0)
        for d in self._notifiers:
            d.callback(None)


    def notifyFinish(self):
        if self._finished:
            return defer.succeed(None)
        else:
            d = defer.Deferred()
            self._notifiers.append(d)
            return d


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
        self.resource = resource.IResource(self.collection)


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

        result = resource.render(request)
        if result is not server.NOT_DONE_YET:
            request.write(result)
            request.finish()

        return request.notifyFinish()


    def _decodeResponse(self):
        """
        Tries to decode the body of a response.
        """
        self.responseContent = json.load(self.request._responseContent)


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
        headers = headers or correctAcceptHeaders
        request = _FakeRequest(args=args, requestHeaders=headers)

        resource = self.resource
        for childName in path:
            resource = resource.getChildWithDefault(childName, request)

        d = self._makeRequest(resource, request)

        @d.addCallback
        def verify(_):
            self._checkContentType()
            self._decodeResponse()

        return d


    def getElements(self, args=None, headers=None):
        """
        Gets a bunch of elements from a collection.
        """
        return self._getResource(args, headers)


    def getElement(self, element, args=None, headers=None):
        """
        Gets a particular element from a collection.
        """
        return self._getResource(args, headers, [element])


    def getElementChild(self, element, child, args=None, headers=None):
        """
        Gets a child of a particular element from a collection.
        """
        return self._getResource(args, headers, [element, child])


    def updateElement(self, name, body, headers=None):
        """
        Update an element.

        For a successful update, the headers should contain a Content-Type.
        """
        request = _FakePUTRequest(body=body, requestHeaders=headers)
        elementResource = self.resource.getChild(name, request)
        return self._makeRequest(elementResource, request)


    def deleteElement(self, name):
        """
        Delete an element.
        """
        request = _FakeDELETERequest()
        elementResource = self.resource.getChild(name, request)
        return self._makeRequest(elementResource, request)


    def createElement(self, name, body, headers=None, method="PUT"):
        """
        Create a new element.
        """
        if method == "PUT":
            return self.updateElement(name, body, headers)
        elif method == "POST":
            request = _FakePOSTRequest(body=body, requestHeaders=headers)
            return self._makeRequest(self.resource, request)
