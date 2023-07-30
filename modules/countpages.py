from renderer.templates import apply_template
from .listpages import query_pages

import renderer
import re


def has_content():
    return True


def render(context, params, content=None):
    # do url params
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

    template = apply_template((content or '').strip(), tpl_vars)

    return renderer.single_pass_render(template, context)
