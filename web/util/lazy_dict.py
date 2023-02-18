from collections.abc import Mapping


# The implementation is not complete; just enough for ListPages
class LazyDict(Mapping):
    def __init__(self, *args, **kw):
        self._raw_dict = dict(*args, **kw)
        self._values_dict = dict()

    def __getitem__(self, key):
        if key in self._values_dict:
            return self._values_dict[key]
        func = self._raw_dict.__getitem__(key)
        v = func() if callable(func) else func
        self._values_dict[key] = v
        return v

    def __setitem__(self, key, value):
        self._raw_dict[key] = value
        try:
            del self._values_dict[key]
        except KeyError:
            pass
        return value

    def __iter__(self):
        return iter(self._raw_dict)

    def __len__(self):
        return len(self._raw_dict)