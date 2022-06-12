# This file implements global variables per thread
# This is so that the state doesn't need to be passed down to each and every handler.
import threading
import copy


_CONTEXTS_LOCK = threading.RLock()
_CONTEXTS = dict()


def register():
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        parent = _CONTEXTS.get(t)
        new_dict = copy.copy(parent or dict())
        new_dict['__parent'] = parent
        _CONTEXTS[t] = new_dict
        return True


def unregister():
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        if t in _CONTEXTS:
            parent = t['__parent']
            if parent:
                _CONTEXTS[t] = parent
            else:
                del _CONTEXTS[t]


def registered():
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        return t in _CONTEXTS


def get(key, default=None):
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        if t in _CONTEXTS:
            return _CONTEXTS[t].get(key, default)
        return default


def put(key, value):
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        if t in _CONTEXTS:
            _CONTEXTS[t][key] = value


class ThreadVarsContext(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.registered = register()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.registered:
            unregister()
        return False


def context():
    return ThreadVarsContext()
