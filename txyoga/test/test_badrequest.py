# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Tests for bad (malformed, nonsensical, ...) requests.
"""
from twisted.web import http, http_headers
from twisted.trial.unittest import TestCase

from txyoga.test import collections


class _BaseFailingRequestTest(collections._PaginatedCollectionMixin):
    """
    Base class for classes that make failing requests.
    """
    def _test_badRequest(self, makeRequest, expectedCode):
        """
        A generic bad request.
        """
        self.addElements()
        makeRequest()
        self._checkBadRequest(expectedCode)


    def _test_badCollectionRequest(self, args=None, headers=None,
                         expectedCode=http.BAD_REQUEST):
        """
        A request for a collection that's expected to fail.
        """
        def makeRequest():
            self.getElements(args, headers)
        self._test_badRequest(makeRequest, expectedCode)


    def _test_badElementRequest(self, name, args=None, headers=None,
                                expectedCode=http.BAD_REQUEST):
        """
        A request for a particular element that's expected to fail.
        """
        def makeRequest():
            self.getElement(name, args, headers)
        self._test_badRequest(makeRequest, expectedCode)



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
