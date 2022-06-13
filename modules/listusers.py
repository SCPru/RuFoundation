import renderer
import re


def has_content():
    return True


def render(context, params, content=None):
    # all params are ignored. always current user
    if not context.user.is_authenticated:
        return ''

    tpl_vars = {
        'number': str(context.user.id),
        'title': context.user.username,
        'name': context.user.username
    }

    template = (content or '').strip()
    template = re.sub(r'(%%(.*?)%%)', lambda var: tpl_vars[var[2]] if var[2] in tpl_vars else '%%'+var[2]+'%%', template)

    return renderer.single_pass_render(template, context)

