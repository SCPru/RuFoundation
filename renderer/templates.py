from typing import Callable
import re


def apply_template(template: str, vars_or_resolver: dict | Callable[[str], str | None]):
    if not callable(vars_or_resolver):
        lower_vars = {k.lower(): v for (k, v) in vars_or_resolver.items()}

        def resolver(name):
            v = lower_vars.get(name.lower(), None)
            return v() if callable(v) else v
    else:
        resolver = vars_or_resolver

    def call_resolver(var) -> str:
        r = resolver(var[2])
        if r is None:
            return '%%' + var[2] + '%%'
        return r

    return re.sub(r'(%%(.*?)%%)', lambda var: call_resolver(var), template)
