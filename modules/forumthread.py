import json
import math

from modules import ModuleError
from modules.listpages import render_date, render_pagination
from renderer import RenderContext, render_template_from_string, render_user_to_html
from renderer.templates import apply_template

import renderer
import re

from renderer.utils import render_user_to_json
from web.controllers import articles, permissions
from web.models.forum import ForumCategory, ForumThread, ForumSection, ForumPost, ForumPostVersion


def has_content():
    return False


def get_post_contents(posts):
    post_ids = [x.id for x in posts]
    post_contents = ForumPostVersion.objects.order_by('post_id', '-created_at').distinct('post_id').filter(post_id__in=post_ids)
    ret = {}
    for content in post_contents:
        ret[content.post_id] = (content.source, content.author)
    return ret


def get_post_info(context, thread, posts):
    post_contents = get_post_contents(posts)
    post_info = []

    for post in posts:
        replies = ForumPost.objects.filter(reply_to=post)
        render_post = {
            'id': post.id,
            'name': post.name,
            'author': render_user_to_html(post.author),
            'created_at': render_date(post.created_at),
            'updated_at': render_date(post.updated_at),
            'content': renderer.single_pass_render(post_contents.get(post.id, ('', None))[0], RenderContext(None, None, {}, context.user)),
            'replies': get_post_info(context, thread, replies),
            'rendered_replies': None,
            'options_config': json.dumps({
                'threadId': thread.id,
                'threadName': thread.name if thread.category_id else thread.article.display_name,
                'postId': post.id,
                'postName': post.name,
                'hasRevisions': post.created_at != post.updated_at,
                'lastRevisionDate': post.updated_at.isoformat(),
                'lastRevisionAuthor': render_user_to_json(post_contents.get(post.id, ('', None))[1]),
                'user': render_user_to_json(context.user),
                'canReply': permissions.check(context.user, 'create', ForumPost(thread=thread)),
                'canEdit': permissions.check(context.user, 'edit', post),
                'canDelete': permissions.check(context.user, 'delete', post),
            })
        }
        post_info.append(render_post)

    return post_info


def render_posts(post_info):
    for i in post_info:
        i['rendered_replies'] = render_posts(i['replies']) if i['replies'] else ''
    return render_template_from_string(
        """
        {% for post in posts %}
        <div class="post-container">
            <div class="post" id="post-{{ post.id }}">
                <div class="long">
                    <div class="head">
                        <div class="title">
                            {{ post.name }}
                        </div>
                        <div class="info">
                            {{ post.author }} <span class="odate" style="display: inline">{{ post.created_at }}</span>
                        </div>
                    </div>
                    <div class="content">
                        {{ post.content }}
                    </div>
                    <div class="options w-forum-post-options" data-config="{{ post.options_config }}"></div>
                </div>
            </div>
            {% if post.replies %}
                {{ post.rendered_replies }}
            {% endif %}
        </div>
        {% endfor %}
        """,
        posts=post_info
    )


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

    category = thread.category
    if not category:
        # find first category that matches
        for c in ForumCategory.objects.filter(is_for_comments=True):
            if permissions.check(context.user, 'view', c):
                category = c
                break

    name = thread.name if thread.category_id else thread.article.display_name

    category_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name))
    short_url = '/forum/t-%d' % thread.id

    # get threads
    page = 1
    try:
        page = int(context.path_params.get('p'))
    except:
        pass
    if page < 1:
        page = 1

    per_page = 10

    q = ForumPost.objects.filter(thread=thread, reply_to__isnull=True)

    total = q.count()

    max_page = max(1, int(math.ceil(total / per_page)))
    if page > max_page:
        page = max_page

    posts = q[(page-1)*per_page:page*per_page]
    post_info = get_post_info(context, thread, posts)

    new_post_config = {
        'threadId': thread.id,
        'threadName': name,
        'user': render_user_to_json(context.user),
    }

    return render_template_from_string(
        """
        <div class="forum-thread-box">
            <div class="forum-breadcrumbs">
                <a href="/forum/start">Форум</a>
                {% if category %}
                &raquo;
                <a href="{{ category_url }}">{{ category.section.name }} / {{ category.name }}</a>
                {% endif %}
                &raquo;
                {{ name }}
            </div>
            <div class="description-block well">
                <div class="statistics">
                    Создатель: {{ created_by }}
                    <br>
                    Дата: <span class="odate" style="display: inline">{{ created_at }}</span>
                    <br>
                    Сообщений: {{ total_posts }}
                </div>
                {% if thread.article %}
                    Это обсуждение страницы <a href="/{{ thread.article.full_name }}">{{ thread.article.display_name }}</a> 
                {% elif thread.description %}
                    <div class="head">
                        Краткое описание:
                    </div>
                    {{ thread.description }}
                {% endif %}
            </div>
            <div class="thread-container" id="thread-container">
                <div id="thread-container-posts">
                    {{ pagination }}
                    {{ posts }}
                    {{ pagination }}
                </div>
            </div>
            {% if can_reply %}
                <div class="w-forum-new-post" data-config="{{ new_post_config }}"></div>
            {% endif %}
        </div>
        """,
        category_url=category_url,
        category=category,
        name=name,
        thread=thread,
        created_by=render_user_to_html(thread.author),
        created_at=render_date(thread.created_at),
        total_posts=total,
        pagination=render_pagination(short_url, page, max_page) if max_page != 1 else '',
        new_post_config=json.dumps(new_post_config),
        posts=render_posts(post_info),
        can_reply=permissions.check(context.user, 'create', ForumPost(thread=thread))
    )
