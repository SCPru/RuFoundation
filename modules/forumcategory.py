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

    c = context.path_params.get('c')
    try:
        c = int(c)
        category = ForumCategory.objects.filter(id=c)
        category = category[0] if category else None
    except:
        category = None

    if category is None:
        context.status = 404
        raise ModuleError('Категория "%s" не найдена' % c)

    sort_by = context.path_params.get('sort')

    num_threads = ForumThread.objects.filter(category=category).count()
    num_posts = ForumPost.objects.filter(thread__category=category).count()

    context.title = category.name

    canonical_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name))
    short_url = '/forum/c-%d' % category.id

    return render_template_from_string(
        """
        <div class="forum-category-box">
            <div class="forum-breadcrumbs">
                <a href="/forum/start">Форум</a>
                &raquo;
                {{ category.section.name }} / {{ category.name }}
            </div>
            <div class="description-block well">
                <div class="statistics">
                    Число тем: {{ num_threads }}
                    <br>
                    Число сообщений: {{ num_posts }}
                </div>
                {{ category.description }}
            </div>
            <div class="options">
                Сортировать по:
                <div>
                    {% if sort_by == 'start' %}
                        <a href="{{ canonical_url }}" class="btn btn-primary btn-small btn-sm">Дате последнего сообщения</a>
                    {% else %}
                        <span class="btn btn-primary disabled btn-small btn-sm"><strong>Дате последнего сообщения</strong></span>
                    {% endif %}
                    <br>
                    {% if sort_by != 'start' %}
                        <a href="{{ short_url }}/sort/start" class="btn btn-primary btn-small btn-sm">Дате открытия темы</a>
                    {% else %}
                        <span class="btn btn-primary disabled btn-small btn-sm"><strong>Дате открытия темы</strong></span>
                    {% endif %}
                </div>
            </div>
            <div class="new-post">
                <a href="/forum:new-thread/c/{{ category.id }}">Создать тему</a>
            </div>
        </div>
        """,
        category=category,
        num_threads=num_threads,
        num_posts=num_posts,
        sort_by=sort_by,
        canonical_url=canonical_url,
        short_url=short_url
    )
