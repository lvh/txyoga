# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Resources providing the REST API to some objects.
"""
from urllib import urlencode
from urlparse import urlsplit, urlunsplit

from twisted.web.resource import IResource, Resource
from twisted.web import http

from txyoga import errors
from txyoga.serializers import json


class RESTErrorPage(Resource):
    """
    An alternative to C{ErrorPage} for REST APIs.

    Wraps a L{SerializableError}, and produces a pretty serializable form.
    """
    def __init__(self, exception, encoder, contentType):
        Resource.__init__(self)

        self.exception = exception
        self.encoder = encoder
        self.contentType = contentType


    def render(self, request):
        request.setHeader("Content-Type", self.contentType)
        request.setResponseCode(self.exception.responseCode)
        return self.encoder(self.exception)



class RESTResourceJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder for REST resources.

    Equivalent to L{json.JSONEncoder}, except it also encodes
    L{SerializableError}s.
    """
    def default(self, obj):
        if isinstance(obj, errors.SerializableError):
            return {"errorMessage": obj.message, "errorDetails": obj.details}
        return json.JSONEncoder.default(self, obj)



def jsonEncode(obj):
    return json.dumps(obj, cls=RESTResourceJSONEncoder)



class Deleted(Resource):
    """
    A resource returned when an element has been successfully deleted.
    """
    def render(self, request):
        request.setResponseCode(http.NO_CONTENT)
        return ""



class EncodingResource(Resource):
    """
    A resource that understands content types.
    """
    encoders = {"application/json": jsonEncode}
    decoders = {"application/json": json.loads}
    defaultMimeType = "application/json"


    def _getEncoder(self, request):
        accept = request.getHeader("Accept") or self.defaultMimeType
        accepted = [mimeType.lower() for mimeType, _ in _parseAccept(accept)]

        for mimeType in accepted:
            try:
                encoder = self.encoders[mimeType]
                request.setHeader("Content-Type", mimeType)
                return encoder, mimeType
            except KeyError:
                continue

        raise errors.UnacceptableRequestError(self.encoders.keys(), accepted)


    def _getDecoder(self, request):
        contentType = request.getHeader("Content-Type")
        if contentType is None:
            supportedTypes = self.decoders.keys()
            raise errors.MissingContentType(supportedTypes)

        try:
            decoder = self.decoders[contentType]
            return decoder, contentType
        except KeyError:
            supportedTypes = self.decoders.keys()
            raise errors.UnsupportedContentTypeError(supportedTypes,
                                                     contentType)



class CollectionResource(EncodingResource):
    """
    A resource representing a REST collection.
    """
    def __init__(self, collection):
        Resource.__init__(self)
        self._collection = collection


    def getChild(self, path, request):
        try:
            if request.method == "DELETE" and not request.postpath:
                # Request wants to delete a child of this collection
                return self._deleteChild(path, request)

            return IResource(self._collection[path])
        except KeyError:
            return self._missingChild(path, request)


    def _deleteChild(self, identifier, request):
        try:
            self._collection.removeByIdentifier(identifier)
            return Deleted()
        except KeyError:
            return self._missingChild(identifier, request)


    def _missingChild(self, element, request):
        e = errors.MissingResourceError("no such element %s" % (element,))

        try:
            encoder, contentType = self._getEncoder(request)
        except errors.UnacceptableRequestError:
            contentType = self.defaultMimeType
            encoder = self.encoders[contentType]

        return RESTErrorPage(e, encoder, contentType)


    def render_GET(self, request):
        mimeType = self.defaultMimeType
        encoder = self.encoders[mimeType]

        try:
            encoder, mimeType = self._getEncoder(request)

            start, stop = self._getBounds(request)
            url = request.prePathURL()
            prevURL, nextURL = self._getPaginationURLs(url, start, stop)

            elements = self._collection[start:stop]
            attrs = self._collection.exposedElementAttributes
            results = [element.toState(attrs) for element in elements]
        except errors.SerializableError, e:
            errorResource = RESTErrorPage(e, encoder, mimeType)
            return errorResource.render(request)

        if (stop - start) > len(elements):
            # Not enough elements -> end of the collection
            nextURL = None

        response = {"results": results, "prev": prevURL, "next": nextURL}
        return encoder(response)


    def _getBounds(self, request):
        """
        Gets the start and stop bounds out of the query.
        """
        try:
            start, = request.args["start"]
        except KeyError:
            start = 0
        except ValueError:
            raise errors.PaginationError("More than one start in query")

        try:
            stop, = request.args["stop"]
        except KeyError:
            stop = self._collection.pageSize
        except ValueError:
            raise errors.PaginationError("More than one stop in query")

        try:
            start = int(start)
        except ValueError:
            raise errors.PaginationError("Start not an integer")

        try:
            stop = int(stop)
        except ValueError:
            raise errors.PaginationError("Stop not an integer")


        return start, stop


    def _getPaginationURLs(self, thisURL, start, stop):
        """
        Produces the URLs for the next page and the previous one.
        """
        scheme, netloc, path, _, _ = urlsplit(thisURL)
        def buildURL(start, stop):
            query = urlencode([("start", start), ("stop", stop)])
            return urlunsplit((scheme, netloc, path, query, ""))

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



class ElementResource(EncodingResource):
    """
    A resource representing an element in a collection.
    """
    encoders = {"application/json": jsonEncode}

    def __init__(self, element):
        Resource.__init__(self)

        self._element = element

        for childName in element.children:
            child = getattr(element, childName)
            self.putChild(childName, IResource(child))


    def render_GET(self, request):
        contentType = self.defaultMimeType
        encoder = self.encoders[self.defaultMimeType]

        try:
            encoder, contentType = self._getEncoder(request)
            state = self._element.toState()
            return encoder(state)
        except errors.SerializableError, e:
            errorResource = RESTErrorPage(e, encoder, contentType)
            return errorResource.render(request)


    def render_PUT(self, request):
        try:
            decoder, contentType = self._getDecoder(request)
            state = decoder(request.body)
            self._element.update(state)
            return ""
        except errors.SerializableError, e:
            contentType = self.defaultMimeType
            encoder = self.encoders[contentType]
            errorResource = RESTErrorPage(e, encoder, contentType)
            return errorResource.render(request)



def _parseAccept(header):
    accepted = []

    for part in header.strip(".").split(","):
        part = part.strip()

        if not part:
            continue # Begone, vile hellspawn!

        elements = part.split(";")
        mimeType, rawParams = elements[0].strip(), elements[1:]
        params = dict(map(str.strip, p.split("=")) for p in rawParams)

        accepted.append((mimeType, params))

    return accepted
