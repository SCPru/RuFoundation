import json

from django.db.models import Q

from modules.forumthread import get_post_contents
from modules.listpages import render_pagination, render_date
from renderer import RenderContext, render_template_from_string, render_user_to_html
import math

import renderer

from renderer.utils import render_vote_to_html
from web.controllers import articles, permissions
from web.models.articles import Vote
from web.models.forum import ForumCategory, ForumSection, ForumPost


def has_content():
    return False


def get_post_info(context, posts, category_for_comments):
    post_contents = get_post_contents(posts)
    post_info = []
    

    for post in posts:
        thread = post.thread
        thread_url = '/forum/t-%d/%s' % (thread.id, articles.normalize_article_name(thread.name if thread.category_id else thread.article.display_name))
        author_vote = ''
        is_op = thread.author == post.author

        if thread.article:
            rating_mode = thread.article.get_settings().rating_mode
            author_vote = Vote.objects.filter(user=post.author, article=thread.article).last()
            author_vote = render_vote_to_html(author_vote, rating_mode)
            if thread.article.author == post.author:
                is_op = True
        
        render_post = {
            'id': post.id,
            'name': post.name.strip() or 'Перейти к сообщению',
            'is_op': is_op,
            'author': render_user_to_html(post.author),
            'author_rate': author_vote,
            'created_at': render_date(post.created_at),
            'content': renderer.single_pass_render(post_contents.get(post.id, ('', None))[0], RenderContext(None, None, {}, context.user), 'message'),
            'url': '%s#post-%d' % (thread_url, post.id),
            'category': {
                'id': post.thread.category.id,
                'name': post.thread.category.name,
                'section_name': post.thread.category.section.name,
                'section_url': '/forum/s-%d/%s' % (post.thread.category.section.id, articles.normalize_article_name(post.thread.category.section.name)),
                'url': '/forum/c-%d/%s' % (post.thread.category.id, articles.normalize_article_name(post.thread.category.name))
            } if post.thread.category_id else {
                'id': category_for_comments.id,
                'name': category_for_comments.name,
                'section_name': category_for_comments.section.name,
                'section_url': '/forum/s-%d/%s' % (category_for_comments.section.id, articles.normalize_article_name(category_for_comments.section.name)),
                'url': '/forum/c-%d/%s' % (category_for_comments.id, articles.normalize_article_name(category_for_comments.name))
            } if category_for_comments else None,
            'thread': {
                'id': post.thread.id,
                'name': post.thread.name if post.thread.category_id else post.thread.article.display_name,
                'url': thread_url
            }
        }
        post_info.append(render_post)

    return post_info


def render(context: RenderContext, params):
    context.title = 'Последние сообщения форума'

    all_categories = [x for x in ForumCategory.objects.order_by('order', 'id') if permissions.check(context.user, 'view', x)]

    category_param = '*'

    try:
        if context.path_params.get('c', '*') != '*':
            view_category = int(context.path_params.get('c'))
            category = ForumCategory.objects.filter(id=view_category)
            category = category[0] if category else None
        else:
            category = None
    except:
        category = None
        all_categories = []

    if category not in all_categories:
        category = None

    if category:
        category_param = category.id

    are_comments_shown = bool([x for x in all_categories if x.is_for_comments])
    if category:
        are_comments_shown = category.is_for_comments

    try:
        page = int(context.path_params.get('p'))
    except:
        page = 1
    if page < 1:
        page = 1

    if category is None:
        if are_comments_shown:
            q = ForumPost.objects.filter(Q(thread__category__in=all_categories) | Q(thread__article__isnull=False))
        else:
            q = ForumPost.objects.filter(thread__category__in=all_categories)
    else:
        if category.is_for_comments:
            q = ForumPost.objects.filter(thread__article__isnull=False)
        else:
            q = ForumPost.objects.filter(thread__category=category)

    q = q.order_by('-created_at')

    per_page = 20

    total = q.count()

    max_page = max(1, int(math.ceil(total / per_page)))
    if page > max_page:
        page = max_page

    category_for_comments = [x for x in all_categories if x.is_for_comments]
    category_for_comments = category_for_comments[0] if category_for_comments else None
    if category and category.is_for_comments:
        category_for_comments = category

    posts = q[(page - 1) * per_page:page * per_page]
    post_info = get_post_info(context, posts, category_for_comments)

    categories = []
    raw_categories = all_categories
    raw_sections = ForumSection.objects.all().order_by('order', 'id')
    for s in raw_sections:
        if not permissions.check(context.user, 'view', s):
            continue
        cs = []
        for c in raw_categories:
            if c.section_id != s.id:
                continue
            cs.append({'name': '\u00a0\u00a0'+c.name, 'canSelect': True, 'id': c.id})
        if cs:
            categories.append({'name': s.name, 'canSelect': False, 'id': None})
            categories += cs

    return render_template_from_string(
        """
        <div class="forum-recent-posts-box w-forum-recent-posts" data-recent-posts-path-params="{{ data_path_params }}" data-recent-posts-params="{{ data_params }}">
            <form onsubmit="return false;" action="" method="get">
                <table class="form">
                <tbody>
                <tr>
                    <td>Из категории:</td>
                    <td>
                        <select id="recent-posts-category">
                            <option value="*"{% if category_param == '*' %} selected{% endif %}>Все категории</option>
                            {% for category in categories %}
                                <option value="{{ category.id }}"{% if not category.canSelect %} disabled{% endif %}{% if category.id == category_param %} selected{% endif %}>
                                    {{ category.name }}
                                </option>
                            {% endfor %}
                        </select>
                        <input class="buttons btn btn-primary" type="button" value="Обновить">
                    </td>
                </tr>
                </tbody>
                </table>
            </form>
            <div id="forum-recent-posts-list">
                <div class="thread-container">
                    {{ pagination }}
                    {% for post in posts %}
                    <div class="post-container">
                        <div class="post" id="post-{{ post.id }}">
                            <div class="long">
                                <div class="head {% if post.is_op %}op-post{% endif %}">
                                    <div class="title">
                                        <a href="{{ post.url }}">{{ post.name }}</a>
                                    </div>
                                    <div class="info">
                                        {{ post.author }} {{ post.created_at }} {{ post.author_rate }}
                                    </div>
                                    <span>
                                        в дискуссии
                                        {% if post.category %}
                                        <a href="{{ post.category.section_url }}">{{ post.category.section_name }}</a> &raquo;
                                        <a href="{{ post.category.url }}">{{post.category.name}}</a> &raquo;
                                        {% endif %}
                                        <a href="{{ post.thread.url}}">{{ post.thread.name }}</a>
                                    </span>
                                </div>
                                <div class="content">
                                    {{ post.content }}
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                    {{ pagination }}
                </div>
            </div>
        </div>
        """,
        posts=post_info,
        categories=categories,
        pagination=render_pagination(None, page, max_page) if max_page != 1 else '',
        data_path_params=json.dumps(context.path_params),
        data_params=json.dumps(params),
        category_param=category_param
    )
