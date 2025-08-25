import json
import math

from modules import ModuleError
from modules.listpages import render_date, render_pagination
from renderer import RenderContext

import renderer

from renderer.utils import render_user_to_json, render_user_to_html, render_template_from_string, render_vote_to_html
from web.controllers import articles, permissions
from web.models.articles import Vote
from web.models.forum import ForumCategory, ForumThread, ForumSection, ForumPost, ForumPostVersion

from ._csrf_protection import csrf_safe_method

def has_content():
    return False


def allow_api():
    return True


def get_post_contents(posts):
    post_ids = [x.id for x in posts]
    post_contents = ForumPostVersion.objects.order_by('post_id', '-created_at').distinct('post_id').filter(post_id__in=post_ids)
    ret = {}
    for content in post_contents:
        ret[content.post_id] = (content.source, content.author)
    return ret


def get_post_info(context, thread, posts, show_replies=True):
    post_contents = get_post_contents(posts)
    post_info = []

    for post in posts:
        replies = ForumPost.objects.filter(reply_to=post).order_by('created_at') if show_replies else []
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
            'name': post.name,
            'is_op': is_op, #e4f0c8
            'author': render_user_to_html(post.author),
            'author_rate': author_vote,
            'created_at': render_date(post.created_at),
            'updated_at': render_date(post.updated_at),
            'content': renderer.single_pass_render(post_contents.get(post.id, ('', None))[0], RenderContext(None, None, {}, context.user), 'message'),
            'replies': get_post_info(context, thread, replies, show_replies),
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
                    <div class="head {% if post.is_op %}op-post{% endif %}">
                        <div class="title">
                            {{ post.name }}
                        </div>
                        <div class="info">
                            {{ post.author }} {{ post.created_at }} {{ post.author_rate }}
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

    content_only = params.get('contentonly', 'no') == 'yes'

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

    if not permissions.check(context.user, 'view', thread):
        raise ModuleError('Недостаточно прав для просмотра темы')

    category = thread.category
    if not category:
        # find first category that matches
        for c in ForumCategory.objects.filter(is_for_comments=True):
            if permissions.check(context.user, 'view', c):
                category = c
                break

    name = thread.name if thread.category_id else thread.article.display_name

    context.title += ' — ' + name

    section_url = '/forum/s-%d/%s' % (category.section.id, articles.normalize_article_name(category.section.name)) if category else ''
    category_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name)) if category else ''
    short_url = '/forum/t-%d' % thread.id

    per_page = 10

    q = ForumPost.objects.filter(thread=thread, reply_to__isnull=True).order_by('created_at')

    total = q.count()

    # get threads
    page = 1
    try:
        page = int(context.path_params.get('p'))
    except:
        # if page is not specified, but post is specified, attempt to guess page number from post id
        try:
            post_id = int(context.path_params.get('post'))
            # if this is a reply, we need to get all the way up to the parent to know what page it is
            post = ForumPost.objects.filter(id=post_id)
            post = post[0] if post else None
            while post:
                if post.thread_id != thread.id:
                    post_id = None
                    break
                if not post.reply_to:
                    break
                post = post.reply_to
                post_id = post.id
            # we now have root post ID.
            # now just get the list of IDs and make a page out of this.
            # not optimized but works for now
            all_posts = list(q.values('id'))
            for i in range(len(all_posts)):
                if all_posts[i]['id'] == post_id:
                    page = int((i / per_page) + 1)
                    break
        except:
            if context.path_params.get('post') is not None:
                raise
            pass
    if page < 1:
        page = 1

    max_page = max(1, int(math.ceil(total / per_page)))
    if page > max_page:
        page = max_page

    posts = q[(page-1)*per_page:page*per_page]
    post_info = get_post_info(context, thread, posts)

    context.path_params['p'] = str(page)

    new_post_config = {
        'threadId': thread.id,
        'threadName': name,
        'user': render_user_to_json(context.user),
    }

    categories = []
    raw_categories = ForumCategory.objects.all().order_by('order', 'id')
    raw_sections = ForumSection.objects.all().order_by('order', 'id')
    for s in raw_sections:
        if not permissions.check(context.user, 'view', s):
            continue
        cs = []
        for c in raw_categories:
            if c.section_id != s.id:
                continue
            if not permissions.check(context.user, 'view', c):
                continue
            cs.append({'name': '\u00a0\u00a0'+c.name, 'canMove': not c.is_for_comments, 'id': c.id})
        if cs:
            categories.append({'name': s.name, 'canMove': False, 'id': None})
            categories += cs

    thread_options_config = {
        'threadId': thread.id,
        'threadName': name,
        'threadDescription': thread.description,
        'canEdit': thread.article_id is None and permissions.check(context.user, 'edit', thread),
        'canPin': thread.article_id is None and permissions.check(context.user, 'pin', thread),
        'canLock': permissions.check(context.user, 'lock', thread),
        'canMove': thread.article_id is None and permissions.check(context.user, 'move', thread),
        'isLocked': thread.is_locked,
        'isPinned': thread.is_pinned,
        'moveTo': categories,
        'categoryId': thread.category_id,
    }

    return render_template_from_string(
        """
        {% if not content_only %}
        <div class="forum-thread-box">
            <div class="forum-breadcrumbs">
                <a href="/forum/start">Форум</a>
                {% if category %}
                &raquo;
                <a href="{{ section_url }}">{{ category.section.name }}</a>
                &raquo;
                <a href="{{ category_url }}">{{ category.name }}</a>
                {% endif %}
                &raquo;
                {{ name }}
            </div>
            <div class="description-block well">
                <div class="statistics">
                    Создатель: {{ created_by }}
                    <br>
                    Дата: {{ created_at }}
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
            <div class="options w-forum-thread-options page-options-bottom" data-config="{{ thread_options_config }}"></div>
            {% endif %}
            <div class="thread-container w-forum-thread"
                 id="thread-container"
                 data-forum-thread-path-params="{{ data_path_params }}"
                 data-forum-thread-params="{{ data_params }}">
                <div id="thread-container-posts">
                    {{ pagination }}
                    {{ posts }}
                    {{ pagination }}
                </div>
            </div>
            {% if can_reply and not content_only %}
                <div class="w-forum-new-post" data-config="{{ new_post_config }}"></div>
            {% endif %}
        </div>
        """,
        section_url=section_url,
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
        can_reply=permissions.check(context.user, 'create', ForumPost(thread=thread)),
        content_only=content_only,
        data_path_params=json.dumps(context.path_params),
        data_params=json.dumps(params),
        thread_options_config=json.dumps(thread_options_config)
    )


@csrf_safe_method
def api_for_article(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    return {"threadId": articles.get_comment_info(context.article)[0]}


def api_update(context, params):
    if 'name' in params:
        if not (params['name'] or '').strip():
            raise ModuleError('Название темы не указано')

    if 'description' in params:
        params['description'] = params['description'] or ''

    t = params.get('threadid')
    try:
        t = int(t)
        thread = ForumThread.objects.filter(id=t)
        thread = thread[0] if thread else None
    except:
        thread = None

    if thread is None:
        context.status = 404
        raise ModuleError('Тема не найдена или не указана')

    if 'name' in params or 'description' in params:
        if not permissions.check(context.user, 'edit', thread):
            raise ModuleError('Недостаточно прав для редактирования темы')
        if 'name' in params:
            thread.name = params['name']
        if 'description' in params:
            thread.description = params['description']

    if 'islocked' in params:
        if not permissions.check(context.user, 'lock', thread):
            raise ModuleError('Недостаточно прав для блокировки темы')
        thread.is_locked = bool(params['islocked'])

    if 'ispinned' in params:
        if not permissions.check(context.user, 'pin', thread):
            raise ModuleError('Недостаточно прав для прикрепления темы')
        thread.is_pinned = bool(params['ispinned'])

    if 'categoryid' in params:
        if not permissions.check(context.user, 'move', thread):
            raise ModuleError('Недостаточно прав для перемещения темы')
        try:
            c = int(params['categoryid'])
            category = ForumCategory.objects.filter(id=c)
            category = category[0] if category else None
            if not permissions.check(context.user, 'view', category):
                raise ModuleError('Недостаточно прав для просмотра целевого раздела')
        except:
            category = None
        if category is None:
            raise ModuleError('Целевой раздел не существует')
        thread.category = category

    thread.save()

    return {
        'threadId': thread.id,
        'name': thread.name,
        'description': thread.description,
        'isLocked': thread.is_locked,
        'isPinned': thread.is_pinned,
        'categoryId': thread.category_id
    }
