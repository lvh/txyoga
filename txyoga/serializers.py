# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Serialization support.
"""
from functools import wraps
from inspect import getargspec
try: # pragma: no cover
    import simplejson as json
except ImportError:# pragma: no cover
    import json

from twisted.web.resource import Resource

from txyoga import errors, interface


def jsonEncode(obj):
    """
    Encodes an object to JSON using the ``RESTResourceJSONEncoder``.
    """
    return json.dumps(obj, cls=RESTResourceJSONEncoder)



class RESTResourceJSONEncoder(json.JSONEncoder):
    """
    A JSON encoder for REST resources.

    Equivalent to ``json.JSONEncoder``, except it also encodes
    ``SerializableError``s.
    """
    def default(self, obj):
        if interface.ISerializableError.providedBy(obj):
            return {"errorMessage": obj.message, "errorDetails": obj.details}
        return json.JSONEncoder.default(self, obj)



class EncodingResource(Resource):
    """
    A resource that understands content types.
    """
    encoders = {"application/json": jsonEncode}
    decoders = {"application/json": json.load}
    defaultContentType = "application/json"


    def _getEncoder(self, request):
        accept = request.getHeader("Accept") or self.defaultContentType
        parsed = _parseAccept(accept)
        accepted = [contentType.lower() for contentType, _ in accepted]

        for contentType in accepted:
            try:
                encoder = self.encoders[contentType]
                request.setHeader("Content-Type", contentType)
                return encoder, contentType
            except KeyError:
                continue

        raise errors.UnacceptableRequest(self.encoders.keys(), accepted)


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
            raise errors.UnsupportedContentType(supportedTypes, contentType)



def reportErrors(m):
    arguments = getargspec(m).args
    renders = "render" in m.__name__

    @wraps(m)
    def wrapper(self, request, *args, **kwargs):
        try:
            contentType = self.defaultContentType
            encoder = self.encoders[contentType]

            if "encoder" in arguments:
                encoder, contentType = self._getEncoder(request)
                kwargs["encoder"] = encoder
            elif "decoder" in arguments:
                decoder, _ = self._getDecoder(request)
                kwargs["decoder"] = decoder

            return m(self, request, *args, **kwargs)
        except errors.SerializableError, e:
            errorResource = errors.RESTErrorPage(e, encoder, contentType)
            return errorResource.render(request) if renders else errorResource

    return wrapper


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
