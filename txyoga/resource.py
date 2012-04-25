# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Resources providing the REST API to some objects.
"""
import functools
import urllib
import urlparse

from twisted.internet import defer
from twisted.python import log
from twisted.web import http, resource, server

from txyoga import errors, interface, serializers


class Created(resource.Resource):
    """
    A resource returned when an element has been successfully created.
    """
    def render(self, request):
        request.setResponseCode(http.CREATED)
        return ""



class Deleted(resource.Resource):
    """
    A resource returned when an element has been successfully deleted.
    """
    def render(self, request):
        request.setResponseCode(http.NO_CONTENT)
        return ""


def deferredRenderWithErrorReporting(method):
    def decorated(self, request):
        d = defer.maybeDeferred(method, self, request)
        d.addErrback(_reportError, request, self.defaultEncoder)
        d.addCallback(_finish, request)
        return server.NOT_DONE_YET

    return decorated


def _reportError(reason, request, defaultEncoder):
    if not interface.ISerializableError.providedBy(reason.value):
        log.err(reason)
        return

    request.encoder = getattr(request, "encoder", defaultEncoder)
    resource = errors.RESTErrorPage(reason.value)
    return resource.render(request)


def _finish(body, request):
    if body is server.NOT_DONE_YET:
        return

    request.write(body)
    request.finish()


def _renderResource(resource, request):
    return resource.render(request)



class DeferredResource(object):
    def __init__(self, deferred, defaultEncoder):
        self.deferred = deferred
        self.defaultEncoder = defaultEncoder


    def getChildWithDefault(self, path, request):
        self.deferred.addCallback(self._getChild, path, request)
        return self


    def _getChild(self, resource, path, request):
        return resource.getChildWithDefault(path, request)


    @deferredRenderWithErrorReporting
    def render(self, request):
        self.deferred.addCallback(_renderResource, request)
        self.deferred.addCallback(_finish, request)
        return self.deferred


    @classmethod
    def returning(cls, method):
        """
        A decorator for methods that return a deferred Resource.
        """
        @functools.wraps(method)
        def decorated(self, *args, **kwargs):
            deferred = defer.maybeDeferred(method, self, *args, **kwargs)
            return cls(deferred, self.defaultEncoder)
        return decorated



class CollectionResource(serializers.EncodingResource):
    """
    A resource representing a REST collection.
    """
    def __init__(self, collection):
        serializers.EncodingResource.__init__(self)
        self._collection = collection


    @DeferredResource.returning
    def getChild(self, path, request):
        """
        Gets the resource for an element in the collection for this resource.

        If this is a DELETE request addressing an element this collection,
        deletes the child. If this is a PUT request request addressing an
        element in this collection, creates the element and adds (upserts)
        it to the collection. Otherwise, attempts to get the child element.
        If that child could not be found, returns an error.

        The case for updating an element is not covered in this method: since
        updating is an operation on elements that already exist, that is
        handled by the corresponding ElementResource.
        """
        if not request.postpath:
            if request.method == "DELETE":
                d = self._collection.remove(path)
                d.addCallback(lambda _: Deleted())
                return d

            elif request.method == "PUT":
                return self._createElement(request, path)

        return self._collection.get(path).addCallback(resource.IResource)


    @serializers.withDecoder
    def _createElement(self, request, identifier=None):
        """
        Attempts to create an element.

        If the request inherently specifies the identifier for the
        element being put (for example, with a PUT request), it is
        specified using the identifier keyword argument. If that
        identifier does not match the identifier of the new element,
        `IdentifierError` is raised.
        """
        state = request.decoder(request.content)
        element = self._collection.createElementFromState(state)

        if identifier is not None:
            actualIdentifier = getattr(element, element.identifyingAttribute)
            if actualIdentifier != identifier:
                e = errors.IdentifierError(identifier, actualIdentifier)
                return defer.fail(e)

        return self._collection.add(element).addCallback(lambda _: Created())


    @deferredRenderWithErrorReporting
    def render_POST(self, request):
        """
        Creates a new element in the collection.
        """
        d = self._createElement(request)
        d.addCallback(_renderResource, request)


    @deferredRenderWithErrorReporting
    def render_GET(self, request):
        """
        Displays the collection.

        If the collection is too large to be displayed at once, it
        will display a part of the collection, one page at a
        time. Each page will have links to the previous and next
        pages.
        """
        request.encoder = self._getEncoder(request)

        start, stop = self._getBounds(request)
        url = request.prePathURL()
        prevURL, nextURL = self._getPaginationURLs(url, start, stop)
        response = {"prev": prevURL, "next": nextURL}

        d = self._collection.query(start=start, stop=stop)

        def _buildResponse(elements):
            attrs = self._collection.exposedElementAttributes
            response["results"] = [e.toState(attrs) for e in elements]
        
            if (stop - start) > len(elements):
                # Not enough elements -> end of the collection
                response["next"] = None

            request.write(request.encoder(response))
            request.finish()

        return d.addCallback(_buildResponse)


    def _getBounds(self, request):
        """
        Gets the start and stop bounds out of the query.
        """
        start = _getBound(request.args, "start")
        stop = _getBound(request.args, "stop", self._collection.pageSize)
        return start, stop


    def _getPaginationURLs(self, thisURL, start, stop):
        """
        Produces the URLs for the next page and the previous one.
        """
        scheme, netloc, path, _, _ = urlparse.urlsplit(thisURL)
        def buildURL(start, stop):
            query = urllib.urlencode([("start", start), ("stop", stop)])
            return urlparse.urlunsplit((scheme, netloc, path, query, ""))

        pageSize = stop - start

        if pageSize < 0:
            raise errors.PaginationError("Requested page size is negative")

        if pageSize > self._collection.maxPageSize:
            raise errors.PaginationError("Requested page size too large")

        prevStart, prevStop = max(0, start - pageSize), start
        if prevStart != prevStop:
            prevURL = buildURL(prevStart, prevStop)
        else:
            prevURL = None

        nextURL = buildURL(stop, stop + pageSize)

        return prevURL, nextURL



def _getBound(args, key, default=0):
    """
    Gets a particular start or stop bound from the given args.
    """
    try:
        values = args[key]
        if len(values) != 1:
            raise errors.PaginationError("duplicate key %s in query" % (key,))

        return int(values[0])
    except KeyError:
        return default
    except ValueError:
        raise errors.PaginationError("key %s not an integer" % (key,))



class ElementResource(serializers.EncodingResource):
    """
    A resource representing an element in a collection.
    """
    def __init__(self, element):
        serializers.EncodingResource.__init__(self)
        self._element = element


    def getChild(self, path, request):
        child = getattr(self._element, path)
        return resource.IResource(child)


    @deferredRenderWithErrorReporting
    @serializers.withEncoder
    def render_GET(self, request):
        """
        Displays the element.
        """
        state = self._element.toState()
        encoded = request.encoder(state)
        request.write(encoded)
        request.finish()


    @deferredRenderWithErrorReporting
    @serializers.withDecoder
    def render_PUT(self, request):
        """
        Updates the element.
        """
        return self._element.update(request.decoder(request.content))
