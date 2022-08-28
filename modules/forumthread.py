from modules import ModuleError
from renderer import RenderContext, render_template_from_string
from renderer.templates import apply_template

import renderer
import re

from web.controllers import articles
from web.models.forum import ForumCategory, ForumThread, ForumSection, ForumPost


def has_content():
    return False


def render(context: RenderContext, params):
    context.title = 'Форум'

    t = context.path_params.get('t')
    try:
        t = int(t)
        thread = ForumThread.objects.filter(id=t)
        thread = thread[0] if thread else None
    except:
        thread = None

    if thread is None:
        context.status = 404
        raise ModuleError('Тема "%s" не найдена' % t)

    return 'threads not supported yet'
