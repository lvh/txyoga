# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Resources providing the REST API to some objects.
"""
from urllib import urlencode
from urlparse import urlsplit, urlunsplit

from twisted.web.resource import IResource, Resource
from twisted.web import http

from txyoga import errors, interface
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
        if interface.ISerializableError.providedBy(obj):
            return {"errorMessage": obj.message, "errorDetails": obj.details}
        return json.JSONEncoder.default(self, obj)



def jsonEncode(obj):
    return json.dumps(obj, cls=RESTResourceJSONEncoder)



class Created(Resource):
    """
    A resource returned when an element has been successfully created.
    """
    def render(self, request):
        request.setResponseCode(http.CREATED)
        return ""



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
    decoders = {"application/json": json.load}
    defaultContentType = "application/json"


    def _getEncoder(self, request):
        accept = request.getHeader("Accept") or self.defaultContentType
        accepted = [contentType.lower() for contentType, _ in _parseAccept(accept)]

        for contentType in accepted:
            try:
                encoder = self.encoders[contentType]
                request.setHeader("Content-Type", contentType)
                return encoder, contentType
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
        """
        Gets the resource for an element in the collection for this resource.

        If this is a DELETE request addressing an element this collection,
        deletes the child.  If it is a PUT request addressing an element in
        this collection which does not exist yet, creates an element
        accessible at the request path.  Otherwise, attempts to return the
        resource for the appropriate addressed child, by accessing that child
        and attempting to adapt it to ``IResource``.

        If that child could not be found, (unless it is being created, of
        course), returns an error page signaling the missing element.

        The case for updating an element is not covered in this method: since
        updating is an operation on elements that already exist, that is
        handled by the corresponding ElementResource.
        """
        try:
            if request.method == "DELETE" and not request.postpath:
                return self._deleteElement(path)

            return IResource(self._collection[path])
        except KeyError:
            # todo: i'm pretty certain we should only allow POST here
            if request.method in ("PUT", "POST") and not request.postpath:
                return self._createElement(path, request)

            return self._missingElement(path, request)


    def _deleteElement(self, identifier):
        """
        Attempts to delete an element.
        """
        self._collection.removeByIdentifier(identifier)
        return Deleted()


    def _createElement(self, identifier, request):
        """
        Attempts to create an element.
        """
        try:
            decoder, contentType = self._getDecoder(request)
            state = decoder(request.content)

            element = self._collection.createElementFromState(state)

            actualIdentifier = getattr(element, element.identifyingAttribute)
            if actualIdentifier != identifier:
                raise errors.IdentifierError(identifier, actualIdentifier)

            self._collection.add(element)
            return Created()
        except errors.SerializableError, e:
            contentType = self.defaultContentType
            encoder = self.encoders[contentType]
            errorResource = RESTErrorPage(e, encoder, contentType)
            return errorResource



    def _missingElement(self, element, request):
        """
        Reports client about a missing element.
        """
        e = errors.MissingResourceError("no such element %s" % (element,))

        try:
            encoder, contentType = self._getEncoder(request)
        except errors.UnacceptableRequestError:
            contentType = self.defaultContentType
            encoder = self.encoders[contentType]

        return RESTErrorPage(e, encoder, contentType)


    def render_GET(self, request):
        """
        Renders the collection.
        """
        contentType = self.defaultContentType
        encoder = self.encoders[contentType]

        try:
            encoder, contentType = self._getEncoder(request)

            start, stop = self._getBounds(request)
            url = request.prePathURL()
            prevURL, nextURL = self._getPaginationURLs(url, start, stop)

            elements = self._collection[start:stop]
            attrs = self._collection.exposedElementAttributes
            results = [element.toState(attrs) for element in elements]
        except errors.SerializableError, e:
            errorResource = RESTErrorPage(e, encoder, contentType)
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
        start = _getBound(request.args, "start")
        stop = _getBound(request.args, "stop", self._collection.pageSize)
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
        contentType = self.defaultContentType
        encoder = self.encoders[self.defaultContentType]

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
            state = decoder(request.content)
            self._element.update(state)
            return ""
        except errors.SerializableError, e:
            contentType = self.defaultContentType
            encoder = self.encoders[contentType]
            errorResource = RESTErrorPage(e, encoder, contentType)
            return errorResource.render(request)

    render_POST = render_PUT



def _parseAccept(header):
    accepted = []

    for part in header.strip(".").split(","):
        part = part.strip()

        if not part:
            continue # Begone, vile hellspawn!

        elements = part.split(";")
        contentType, rawParams = elements[0].strip(), elements[1:]

        params = {}
        for param in rawParams:
            key, value = map(str.strip, param.split("=", 1))
            params[key] = value

        accepted.append((contentType, params))

    return accepted
