# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Access to serialization modules.
"""
from functools import wraps
try: # pragma: no cover
    import simplejson as json
except ImportError:# pragma: no cover
    import json

from txyoga import errors


def decodes(renders=True):
    def decorator(m):
        @wraps(m)
        def wrapper(self, request):
            try:
                decoder, _ = self._getDecoder(request)
                return m(self, request, decoder)
            except errors.SerializableError, e:
                contentType = self.defaultContentType
                encoder = self.encoders[contentType]
                errorResource = errors.RESTErrorPage(e, encoder, contentType)

                if renders:
                    return errorResource.render(request)
                else:
                    return errorResource

        return wrapper
    return decorator
