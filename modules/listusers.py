import renderer
from django.conf import settings

from renderer.templates import apply_template


def has_content():
    return True


def render(context, params, content=None):
    # all params are ignored. always current user
    if not context.user.is_authenticated:
        if params.get('always', 'no') != 'yes':
            return ''
        tpl_vars = {}
    else:
        tpl_vars = {
            'number': str(context.user.id),
            'title': context.user.username,
            'name': context.user.username,
            'avatar': context.user.get_avatar(settings.DEFAULT_AVATAR)
        }

    template = apply_template((content or '').strip(), tpl_vars)

    return renderer.single_pass_render(template, context)

