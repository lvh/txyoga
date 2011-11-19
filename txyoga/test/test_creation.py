# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Test creating elements in collections
"""
from twisted.trial.unittest import TestCase
from twisted.web import http, http_headers

from txyoga.test import collections
from txyoga.serializers import json


class ElementCreationTest(collections.ElementCreationMixin):
    """
    Test creating elements. 
    """
    def setUp(self):
        collections.ElementCreationMixin.setUp(self)
        self.requestBody = json.dumps(self.newElementState)
        self.headers = http_headers.Headers()


    def createTestElement(self):
        name, body = self.newElementName, self.requestBody
        self.createElement(name, body, self.headers, self.method)


    def getTestElement(self):
        self.getElement(self.newElementName)


    def _test_createElement(self, expectedStatusCode=http.CREATED):
        self.createTestElement()

        if expectedStatusCode is http.CREATED:
            self.assertEqual(self.request.code, expectedStatusCode)
            self._checkContentType(None)

            self.getTestElement()
            self.assertEqual(self.request.code, http.OK)
            self._checkContentType("application/json")
            self._decodeResponse()
            self.assertEqual(self.responseContent, self.newElementState)
        else: 
            self._checkContentType("application/json")
            self._decodeResponse()
            self._checkBadRequest(expectedStatusCode)


    def test_simple(self):
        """
        Tests that creating an element works.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self._test_createElement(http.CREATED)


    def test_missingContentType(self):
        """
        Tests that creating an element when not specifying the content
        type fails.
        """
        self._test_createElement(http.UNSUPPORTED_MEDIA_TYPE)


    def test_badContentType(self):
        """
        Tests that creating an element when specifying a bad content
        type fails.
        """
        self.headers.setRawHeaders("Content-Type", ["ZALGO/ZALGO"])
        self._test_createElement(http.UNSUPPORTED_MEDIA_TYPE)



class POSTElementCreationTest(ElementCreationTest, TestCase):
    method = "POST"



class PUTElementCreationTest(ElementCreationTest, TestCase):
    method = "PUT"

    def test_wrongName(self):
        self.headers.setRawHeaders("Content-Type", ["application/json"])

        self.newElementName = "BOGUS"
        self._test_createElement(http.FORBIDDEN)
        del self.newElementName
