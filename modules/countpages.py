from renderer.templates import apply_template
from ._csrf_protection import csrf_safe_method
from .listpages import query_pages

import renderer
import re


def allow_api():
    return True


def has_content():
    return True


@csrf_safe_method
def api_get(context, params):
    for k, v in params.items():
        if v[:5].lower() == '@url|':
            default = v[5:]
            if k in context.path_params:
                params[k] = context.path_params[k]
            else:
                params[k] = default

    total = str(len(query_pages(context.article, params, context.user, context.path_params, False)[0]))

    tpl_vars = {
        'total': total,
        'count': total,
    }

    return tpl_vars 


def render(context, params, content=None):
    tpl_vars = api_get(context, params)

    template = apply_template((content or '').strip(), tpl_vars)

    return renderer.single_pass_render(template, context)
