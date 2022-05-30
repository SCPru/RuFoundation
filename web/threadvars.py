# This file implements global variables per thread
# This is so that the state doesn't need to be passed down to each and every handler.
import threading


_CONTEXTS_LOCK = threading.RLock()
_CONTEXTS = dict()


def register():
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        if t not in _CONTEXTS:
            #print('register %s' % repr(t))
            _CONTEXTS[t] = dict()
            return True
        return False


def unregister():
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        #print('unregister %s' % repr(t))
        if t in _CONTEXTS:
            del _CONTEXTS[t]


def registered():
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        return t in _CONTEXTS


def get(key, default=None):
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        #print('get %s [%s]' % (repr(t), repr(key)))
        if t in _CONTEXTS:
            return _CONTEXTS[t].get(key, default)
        return default


def put(key, value):
    with _CONTEXTS_LOCK:
        t = threading.current_thread().ident
        #print('put %s [%s] = %s' % (repr(t), repr(key), repr(value)))
        if t in _CONTEXTS:
            _CONTEXTS[t][key] = value


class context(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.registered = register()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.registered:
            unregister()
        return True


