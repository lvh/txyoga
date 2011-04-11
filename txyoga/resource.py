# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Resources providing the REST API to some objects.
"""
from urllib import urlencode
from urlparse import urlsplit, urlunsplit
from zope.interface import implements

from twisted.web.resource import IResource, Resource
from twisted.web import http

from txyoga.interface import ISerializableError
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



class SerializableError(Exception):
    """
    An error that can be serialized.
    """
    implements(ISerializableError)
    responseCode = http.BAD_REQUEST

    def __init__(self, message, details=None):
        self.message = message
        self.details = details if details is not None else {}



class UnsupportedContentTypeError(SerializableError):
    """
    Raised when the provided media type is unsupported.

    This happens on POST or PUT.
    """
    responseCode = http.UNSUPPORTED_MEDIA_TYPE

    def __init__(self, supportedMimeTypes, providedMimeType):
        message = "no acceptable decoder available for given MIME type"
        details = {"supportedMimeTypes": supportedMimeTypes,
                   "providedMimeType": providedMimeType}
        SerializableError.__init__(self, message, details)



class MissingContentType(SerializableError):
    """
    Raised when the client forgot to specify the content type.
    """
    responseCode = http.UNSUPPORTED_MEDIA_TYPE

    def __init__(self, supportedMimeTypes):
        message = "request didn't specify a content type"
        details = {"supportedMimeTypes": supportedMimeTypes}
        SerializableError.__init__(self, message, details)



class UnacceptableRequestError(SerializableError):
    """
    Raised when the requested resource could not be provided in one of the
    accepted content types.

    This happens on GET.
    """
    responseCode = http.NOT_ACCEPTABLE

    def __init__(self, supportedMimeTypes, acceptedMimeTypes):
        message = "no acceptable encoder available"
        details = {"supportedMimeTypes": supportedMimeTypes,
                   "acceptedMimeTypes": acceptedMimeTypes}
        SerializableError.__init__(self, message, details)



class PaginationError(SerializableError):
    """
    Raised when there was a problem computing pagination.
    """



class MissingResourceError(SerializableError):
    """
    Describes a missing resource.
    """
    responseCode = http.NOT_FOUND



class RESTResourceJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder for REST resources.

    Equivalent to L{json.JSONEncoder}, except it also encodes
    L{SerializableError}s.
    """
    def default(self, obj):
        if isinstance(obj, SerializableError):
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

        raise UnacceptableRequestError(self.encoders.keys(), accepted)


    def _getDecoder(self, request):
        contentType = request.getHeader("Content-Type")
        if contentType is None:
            supportedTypes = self.decoders.keys()
            raise MissingContentType(supportedTypes)

        try:
            decoder = self.decoders[contentType]
            return decoder, contentType
        except KeyError:
            supportedTypes = self.decoders.keys()
            raise UnsupportedContentTypeError(supportedTypes, contentType)



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
        error = MissingResourceError("no such element %s" % (element,))

        try:
            encoder, contentType = self._getEncoder(request)
        except UnacceptableRequestError:
            contentType = self.defaultMimeType
            encoder = self.encoders[contentType]

        return RESTErrorPage(error, encoder, contentType)


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
        except SerializableError, e:
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
            raise PaginationError("More than one start in query")

        try:
            stop, = request.args["stop"]
        except KeyError:
            stop = self._collection.pageSize
        except ValueError:
            raise PaginationError("More than one stop in query")

        try:
            start, stop = int(start), int(stop)
        except ValueError:
            raise PaginationError("Start or stop not (decimal) integers")

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
            raise PaginationError("Bad page size (stop before start)")

        if pageSize > self._collection.maxPageSize:
            raise PaginationError("Requested page size too large")

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

        for collectionName in element.children:
            collection = getattr(element, collectionName)
            self.putChild(collectionName, IResource(collection))


    def render_GET(self, request):
        contentType = self.defaultMimeType
        encoder = self.encoders[self.defaultMimeType]

        try:
            encoder, contentType = self._getEncoder(request)
            state = self._element.toState()
            return encoder(state)
        except SerializableError, e:
            errorResource = RESTErrorPage(e, encoder, contentType)
            return errorResource.render(request)


    def render_PUT(self, request):
        try:
            decoder, contentType = self._getDecoder(request)
            state = decoder(request.body)
            self._element.update(state)
            return ""
        except SerializableError, e:
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
