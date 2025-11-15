from django.conf import settings

import renderer
from renderer.parser import RenderContext
from renderer.templates import apply_template
from renderer.utils import get_boolean_param, render_user_to_html, render_user_to_text


def allow_api():
    return True


def has_content():
    return True


def render(context: RenderContext, params, content=None):
    if not context.user.is_authenticated and not get_boolean_param(params, 'always'):
        return ''
    
    templates = []
    
    for author in context.article.authors.all():
        tpl_vars = {
            'author': lambda: render_user_to_text(author),
            'author_linked': lambda: render_user_to_html(author)
        }
        templates.append(apply_template((content or '').strip(), tpl_vars))

    return renderer.single_pass_render(' '.join(templates), context)

