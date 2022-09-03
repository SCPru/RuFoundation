from modules import ModuleError
from modules.listpages import render_pagination, render_date
from renderer import RenderContext, render_template_from_string, render_user_to_html
import math
from renderer.templates import apply_template

import renderer
import re

from web.controllers import articles, permissions
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

    if not permissions.check(context.user, 'view', category):
        raise ModuleError('Недостаточно прав для просмотра раздела')

    sort_by = context.path_params.get('sort')

    num_threads = ForumThread.objects.filter(category=category).count()
    num_posts = ForumPost.objects.filter(thread__category=category).count()

    context.title = category.name

    canonical_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name))
    short_url = '/forum/c-%d' % category.id

    # get threads
    page = 1
    try:
        page = int(context.path_params.get('p'))
    except:
        pass
    if page < 1:
        page = 1

    per_page = 20

    q = ForumThread.objects

    if category.is_for_comments:
        q = q.filter(article_id__isnull=False)
    else:
        q = q.filter(category=category)

    if sort_by != 'start':
        q = q.order_by('-is_pinned', '-updated_at')
    else:
        q = q.order_by('-is_pinned', '-created_at')
    total = q.count()

    max_page = max(1, int(math.ceil(total / per_page)))
    if page > max_page:
        page = max_page

    threads = q[(page-1)*per_page:page*per_page]
    render_threads = []
    for thread in threads:
        posts = ForumPost.objects.filter(thread=thread).order_by('created_at')
        post_count = posts.count()
        last_post_url = None
        last_post_user = None
        last_post_date = None
        url = '/forum/t-%d/%s' % (thread.id, articles.normalize_article_name(thread.name if thread.category_id else thread.article.display_name))
        if post_count:
            last_post = posts[post_count-1]  # do not use -1 to avoid checking count twice
            last_post_url = '%s#post-%d' % (url, last_post.id)
            last_post_date = render_date(last_post.created_at)
            last_post_user = render_user_to_html(last_post.author)
        render_threads.append({
            'name': thread.name if thread.category_id else thread.article.display_name,
            'description': thread.description,
            'created_by': render_user_to_html(thread.author),
            'created_at': render_date(thread.created_at),
            'post_count': post_count,
            'url': url,
            'last_post_url': last_post_url,
            'last_post_date': last_post_date,
            'last_post_user': last_post_user,
            'is_pinned': thread.is_pinned,
            'is_locked': thread.is_locked,
        })

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
            {{ pagination }}
            <table class="table" style="width: 98%">
            <tbody>
            <tr class="head">
                <td>Название темы</td>
                <td>Создано</td>
                <td>Сообщений</td>
                <td>Последнее сообщение</td>
            </tr>
            {% for thread in threads %}
                <tr>
                    <td class="name">
                        <div class="title">
                            {% if thread.is_pinned %}
                            Закреплено: 
                            {% endif %}
                            <a href="{{ thread.url }}">{{ thread.name }}</a>
                        </div>
                        <div class="description">{{ thread.description }}</div>
                    </td>
                    <td class="started">
                        Автор: {{ thread.created_by }}
                        <br>
                        {{ thread.created_at }}
                    </td>
                    <td class="posts">
                        {{ thread.post_count }}
                    </td>
                    <td class="last">
                        {% if thread.last_post_url %}
                        Автор: {{ thread.last_post_user }}
                        <br>
                        {{ thread.last_post_date }}
                        <br>
                        <a href="{{ thread.last_post_url }}">Перейти</a>
                        {% endif %}
                    </td>
                </tr>
            {% endfor %}
            </tbody>
            </table>
            {{ pagination }}
        </div>
        """,
        category=category,
        num_threads=num_threads,
        num_posts=num_posts,
        sort_by=sort_by,
        canonical_url=canonical_url,
        short_url=short_url,
        threads=render_threads,
        pagination=render_pagination(short_url, page, max_page) if max_page != 1 else ''
    )
