"""
Access to serialization modules.
"""
# JSON is used extensively and we want to support people using simplejson (it
# might have the fast C extension, and for people with older Python versions)
# so to not have to copy the try/except block, we import it once here.
try: # pragma: no cover
    import simplejson as json
except ImportError:# pragma: no cover
    import json
