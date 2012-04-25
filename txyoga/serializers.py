# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txyoga authors. See the LICENSE file for details.
"""
Serialization support.
"""
import functools
try: # pragma: no cover
    import simplejson as json
except ImportError:# pragma: no cover
    import json

from twisted.web.resource import Resource

from txyoga import errors, interface


def forContentType(contentType):
    def decorator(encoder):
        encoder.contentType = contentType
        return encoder
    return decorator


@forContentType("application/json")
def jsonDecode(state):
    """
    Decodes an object from JSON.
    """
    return json.load(state)


@forContentType("application/json")
def jsonEncode(obj):
    """
    Encodes an object to JSON using the ``_RESTResourceJSONEncoder``.
    """
    return json.dumps(obj, cls=_RESTResourceJSONEncoder)



class _RESTResourceJSONEncoder(json.JSONEncoder):
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
    defaultEncoder = staticmethod(jsonEncode)
    encoders = [jsonEncode]
    decoders = [jsonDecode]


    def _getEncoder(self, request):
        accept = request.getHeader("Accept")

        if accept is None:
            self._unacceptable()

        parsed = _parseAccept(accept)
        accepted = [contentType.lower() for contentType, _ in parsed]

        for contentType in accepted:
            for encoder in self.encoders:
                if encoder.contentType == contentType:
                    request.setHeader("Content-Type", encoder.contentType)
                    return encoder

        self._unacceptable(accepted)


    def _unacceptable(self, accepted=None):
        supported = [encoder.contentType for encoder in self.encoders]
        raise errors.UnacceptableRequest(supported, accepted)


    def _getDecoder(self, request):
        contentType = request.getHeader("Content-Type")
        if contentType is None:
            supported = [decoder.contentType for decoder in self.decoders]
            raise errors.MissingContentType(supported)

        for decoder in self.decoders:
            if decoder.contentType == contentType:
                return decoder

        supported = [decoder.contentType for decoder in self.decoders]
        raise errors.UnsupportedContentType(supported, contentType)



def withEncoder(m):
    """
    Tacks the appropriate encoder on to a decorated method's request.
    """
    @functools.wraps(m)
    def decorated(self, request, *args, **kwargs):
        request.encoder = self._getEncoder(request)
        return m(self, request, *args, **kwargs)
    return decorated


def withDecoder(m):
    """
    Tacks the appropriate decoder on to a decorated method's request.
    """
    @functools.wraps(m)
    def decorated(self, request, *args, **kwargs):
        request.decoder = self._getDecoder(request)
        return m(self, request, *args, **kwargs)
    return decorated


def _parseAccept(header):
    """
    Parses an Accept header.

    Returns an iterable of 2-tuples with the content type and the
    matching parameters. The parameters is a dictionary with the
    key-value pairs of the parameters. This dictionary should either
    be empty or contain a single key (``"q"``). The matching value
    determines the preference of the client for that content type.
    """
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
