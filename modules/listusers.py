import logging
from django.conf import settings

import renderer
from renderer.templates import apply_template
from renderer.utils import get_boolean_param, render_user_to_html, render_user_to_text

from ._csrf_protection import csrf_safe_method


def allow_api():
    return True


def has_content():
    return True


@csrf_safe_method
def api_get(context, params):
    is_authenticated = context.user.is_authenticated
    number = str(context.user.id) if is_authenticated else '-1'
    name = context.user.username if is_authenticated else params.get('anonname', '[АНОНИМ]')
    avatar = context.user.get_avatar(settings.DEFAULT_AVATAR)
    return {
        'number': number,
        'title': name,
        'name': name,
        'avatar': avatar,
        'is_authenticated': True
    }


def render(context, params, content=None):
    templates = []
    if get_boolean_param(params, 'authors'):
        for author in context.article.authors.all():
            tpl_vars = {
                'author': lambda: render_user_to_text(author),
                'author_linked': lambda: render_user_to_html(author)
            }
            templates.append(apply_template((content or '').strip(), tpl_vars))
    else:
        # Always current user
        if not context.user.is_authenticated and not get_boolean_param(params, 'always'):
            return ''
        tpl_vars = api_get(context, params)
        templates.append(apply_template((content or '').strip(), tpl_vars))

    return renderer.single_pass_render(' '.join(templates), context)

