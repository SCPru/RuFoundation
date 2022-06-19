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

    template = (content or '').strip()
    template = re.sub(r'(%%(.*?)%%)', lambda var: tpl_vars[var[2]] if var[2] in tpl_vars else '%%'+var[2]+'%%', template)

    return renderer.single_pass_render(template, context)
