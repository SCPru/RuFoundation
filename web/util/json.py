__all__ = [
    'replace_json_dumps_default'
]

import json
from json import dump as _dump
from json import dumps as _dumps

from web.util.pydantic import JSONInterface


def get_default(_default=None, **kwargs):
    if 'default' in kwargs:
        _default = kwargs['default']
    def default(o):
        if isinstance(o, JSONInterface):
            return o.dump()
        if _default:
            return _default(o)
    return default


def dump(*args, **kwargs):
    kwargs['default'] = get_default(**kwargs)
    return _dump(*args, **kwargs)


def dumps(*args, **kwargs):
    kwargs['default'] = get_default(**kwargs)
    return _dumps(*args, **kwargs)


def replace_json_dumps_default():
    json.dump = dump
    json.dumps = dumps
