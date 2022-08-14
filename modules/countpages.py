from renderer.templates import apply_template
from .listpages import query_pages

import renderer
import re


def has_content():
    return True


def render(context, params, content=None):
    total = str(len(query_pages(context, params, False)[0]))

    tpl_vars = {
        'total': total,
        'count': total,
    }

    template = apply_template((content or '').strip(), tpl_vars)

    return renderer.single_pass_render(template, context)
