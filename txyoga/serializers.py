# -*- coding: utf-8 -*-
# Copyright (c), 2011, the txYoga authors. See the LICENSE file for details.
"""
Access to serialization modules.
"""
try: # pragma: no cover
    import simplejson as json
except ImportError:# pragma: no cover
    import json

from txyoga import errors


def decodes(m):
    def render(self, request):
        try:
            decoder, _ = self._getDecoder(request)
            return m(self, request, decoder)
        except errors.SerializableError, e:
            contentType = self.defaultContentType
            encoder = self.encoders[contentType]
            errorResource = errors.RESTErrorPage(e, encoder, contentType)
            return errorResource.render(request)

    return render
