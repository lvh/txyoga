# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Exceptions for stores.
"""
class UnknownCollectionError(RuntimeError):
    """
    Raised when attemption to interact with a collection unknown to a store.
    """
    def __init__(self, collection, store):
        message = "{0} doesn't have {1}".format(store, collection)
        RuntimeError.__init__(self, message)



class DuplicateElementError(RuntimeError):
    """
    Raised when an element is added to a store that already has an element
    with that identifier.
    """
    def __init__(self, identifier):
        message = "duplicate element: {0}".format(identifier)
        RuntimeError.__init__(self, message)



class MissingElementError(RuntimeError):
    """
    An exception raised when an element that was expected to exist didn't.

    This could be raised when attempting to remove or get an element.
    """
    def __init__(self, identifier):
        message = "missing element: {0}".format(identifier)
        RuntimeError.__init__(self, message)