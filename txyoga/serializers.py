# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Access to serialization modules.
"""
from functools import wraps
from inspect import getargspec
try: # pragma: no cover
    import simplejson as json
except ImportError:# pragma: no cover
    import json

from txyoga import errors


ADDED_KEYS = frozenset(["encoder", "decoder"])


def reportErrors(m):
    needs, = (ADDED_KEYS & set(getargspec(m).args)) or [None]
    renders = "render" in m.__name__

    @wraps(m)
    def wrapper(self, request, *args, **kwargs):
        try:
            if needs == "encoder":
                contentType = self.defaultContentType
                encoder = self.encoders[contentType]
                encoder, contentType = self._getEncoder(request)
                kwargs["encoder"] = encoder
            elif needs == "decoder":
                decoder, _ = self._getDecoder(request)
                kwargs["decoder"] = decoder

            return m(self, request=request, *args, **kwargs)
        except errors.SerializableError, e:
            if needs == "decoder":
                contentType = self.defaultContentType
                encoder = self.encoders[contentType]

            errorResource = errors.RESTErrorPage(e, encoder, contentType)
            if renders:
                return errorResource.render(request)
            else:
                return errorResource

    return wrapper
