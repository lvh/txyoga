# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Test updating elements in collections.
"""
from twisted.trial.unittest import TestCase
from twisted.web import http, http_headers

from txyoga.errors import AttributeValueUpdateError
from txyoga.serializers import json
from txyoga.test import collections


allowedUpdateState = {"color": "green"}
nilpotentUpdateState = {"maximumOccupancy": 100}
disallowedUpdateState = {"maximumOccupancy": 200}
disallowedUpdateStateWithHiddenAttribute = {"name": "south"}



class ElementUpdatingTest(collections.UpdatableCollectionMixin, TestCase):
    """
    Test the updating of elements.
    """
    def setUp(self):
        collections.UpdatableCollectionMixin.setUp(self)
        self.addElements()
        self.headers = http_headers.Headers()
        self.body = allowedUpdateState


    def _testUpdate(self, expectedStatusCode=http.OK):
        """
        Tries to change the color of a bikeshed.
        """
        name = self.elementArgs[0][0]
        self.getElement(name)
        expectedContent = self.responseContent

        encodedBody = json.dumps(self.body)
        self.updateElement(name, encodedBody, self.headers)

        if expectedStatusCode is http.OK:
            # A successful PUT does not have a response body
            self.assertEqual(self.request.code, expectedStatusCode)
            self._checkContentType(None)
            expectedContent["color"] = self.body["color"]
        else:
            # A failed PUT has a response body
            self._checkContentType("application/json")
            self._decodeResponse()
            self._checkBadRequest(expectedStatusCode)

        self.getElement(name)
        self.assertEqual(self.request.code, http.OK)
        self._checkContentType("application/json")
        self.assertEqual(self.responseContent, expectedContent)


    def test_simple(self):
        """
        Test that updating an element works.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self._testUpdate()


    def test_missingContentType(self):
        """
        Test that trying to update an element when not specifying the content
        type fails.
        """
        self._testUpdate(http.UNSUPPORTED_MEDIA_TYPE)


    def test_badContentType(self):
        """
        Test that trying to update an element when specifying a bad content
        type fails.
        """
        self.headers.setRawHeaders("Content-Type", ["ZALGO/ZALGO"])
        self._testUpdate(http.UNSUPPORTED_MEDIA_TYPE)


    def test_nonUpdatableAttribute(self):
        """
        Tests that updating an attribute which is not allowed to be updated
        responds that that operation is forbidden.

        Try to make the bikeshed twice as large, which won't work because that
        would be a useful change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = disallowedUpdateState
        self._testUpdate(http.FORBIDDEN)


    def test_partiallyUpdatableAttributes(self):
        """
        Tests that updates are atomic; when part of an update is not allowed,
        the entire update does not happen.

        Try to make the bikeshed twice as large and change its color.  Both
        will fail, since the useful operation blocks the entire change.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = dict(disallowedUpdateState, **allowedUpdateState)
        self._testUpdate(http.FORBIDDEN)


    def test_completeState(self):
        """
        Tests that an update with complete state works.

        This means that there are attributes in the new state that are
        updatable, but are the same as the current value, so the
        update is nilpotent.
        """
        self.headers.setRawHeaders("Content-Type", ["application/json"])
        self.body = dict(allowedUpdateState, **nilpotentUpdateState)
        self._testUpdate()



class ManualUpdatingTest(collections.UpdatableCollectionMixin, TestCase):
    """
    Tests updating an element directly.
    """
    def setUp(self):
        collections.UpdatableCollectionMixin.setUp(self)
        self.addElements()
        firstElementIdentifier = self.elementArgs[0][0]
        self.element = self.collection[firstElementIdentifier]
        self.originalState = self.element.toState()


    def _testUpdate(self, state, exceptionClass=None, exposesValue=True):
        if exceptionClass is None:
            self.element.update(state)
            expectedState = state
        else:
            try:
                self.element.update(state)
                self.fail() # pragma: no cover
            except exceptionClass, e:
                if exposesValue:
                    self.assertIn("currentValue", e.details)
                else:
                    self.assertNotIn("currentValue", e.details)
                
            expectedState = self.originalState

        for attribute, value in expectedState.iteritems():
            self.assertEqual(getattr(self.element, attribute), value)


    def test_nonUpdatableAttribute(self):
        state = dict(disallowedUpdateState)
        self._testUpdate(state, AttributeValueUpdateError)


    def test_nonUpdatableAttribute_dontLeakValue(self):
        state = dict(disallowedUpdateStateWithHiddenAttribute)
        self._testUpdate(state, AttributeValueUpdateError, False)


    def test_partiallyUpdatableAttributes(self):
        state = dict(disallowedUpdateState, **allowedUpdateState)
        self._testUpdate(state, AttributeValueUpdateError)


    def test_completeState(self):
        state = dict(allowedUpdateState, **nilpotentUpdateState)
        self._testUpdate(state)
