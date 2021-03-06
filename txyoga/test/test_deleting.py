# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Test deleting elements from collections.
"""
from twisted.trial.unittest import TestCase
from twisted.web import http

from txyoga.test import collections


class ElementDeletionTest(collections.SimpleCollectionMixin, TestCase):
    """
    Tests the deletion elements from a collection.
    """
    def setUp(self):
        collections.SimpleCollectionMixin.setUp(self)
        self.addElements()


    def _checkSuccessfulDeletion(self, _):
        """
        Test that deleting an element succeeded.
        """
        self.assertEqual(self.request.code, http.NO_CONTENT)
        self._checkContentType(None)


    def _checkFailedDeletion(self, _):
        """
        Test that deleting an element failed as expected.
        """
        # A failed DELETE has a response body, check it
        self._checkContentType("application/json")
        self._decodeResponse()
        self._checkBadRequest(http.NOT_FOUND)


    def test_deleteElement(self):
        """
        Delete an element, check response.
        """
        name = self.elementArgs[0][0]
        d = self.deleteElement(name)
        d.addCallback(self._checkSuccessfulDeletion)
        return d


    def test_deleteMissingElement(self):
        """
        Delete an element that doesn't exist, check response.
        """
        d = self.deleteElement("bogus")
        d.addCallback(self._checkFailedDeletion)
        return d


    def test_deleteElementTwice(self):
        """
        Delete an element, check response, delete it again, check response.
        """
        name = self.elementArgs[0][0]
        d = self.deleteElement(name)
        d.addCallback(self._checkSuccessfulDeletion)
        d.addCallback(lambda _: self.deleteElement(name))
        d.addCallback(self._checkFailedDeletion)
        return d
