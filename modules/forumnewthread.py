from modules import ModuleError
from renderer import RenderContext, render_template_from_string, single_pass_render
import json

from renderer.utils import render_user_to_json
from web.controllers import articles, permissions
from web.models.forum import ForumCategory, ForumThread, ForumPost, ForumPostVersion


def has_content():
    return False


def render(context: RenderContext, params):
    context.title = 'Создать тему'

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

    if not permissions.check(context.user, 'create', ForumThread(category=category)):
        raise ModuleError('Недостаточно прав для создания темы')

    num_threads = ForumThread.objects.filter(category=category).count()
    num_posts = ForumPost.objects.filter(thread__category=category).count()

    canonical_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name))

    editor_config = {
        'type': 'new_thread',
        'categoryId': category.id,
        'user': render_user_to_json(context.user),
        'cancelUrl': canonical_url
    }

    return render_template_from_string(
        """
        <div class="forum-new-thread-box">
            <div class="forum-breadcrumbs">
                <a href="/forum/start">Форум</a>
                &raquo;
                <a href="{{ canonical_url }}">{{ breadcrumb }}</a>
                &raquo;
                Создать тему
            </div>
            <div class="description well">
                <div class="statistics">
                    Число тем: {{ num_threads }}
                    <br>
                    Число сообщений: {{ num_posts }}
                </div>
                {{ description }}
            </div>
        </div>
        <!-- lets fucking hope no one attempted to style the forum page -->
        <div id="w-forum-new-thread" data-config="{{ editor_config }}"></div>
        """,
        breadcrumb='%s / %s' % (category.section.name, category.name),
        description=category.description,
        num_threads=num_threads,
        num_posts=num_posts,
        canonical_url=canonical_url,
        editor_config=json.dumps(editor_config)
    )


def allow_api():
    return True


def api_preview(context, params):
    if 'source' not in params:
        raise ModuleError('Исходный код не указан')

    return {'result': single_pass_render(params['source'], RenderContext(None, None, {}, context.user))}


def api_submit(context, params):
    title = (params.get('title') or '').strip()
    description = (params.get('description') or '').strip()[:1000]
    source = (params.get('source') or '').strip()

    if not title:
        raise ModuleError('Не указано название темы')

    if not source:
        raise ModuleError('Не указан текст первого сообщения')

    c = params.get('categoryId')
    try:
        c = int(c)
        category = ForumCategory.objects.filter(id=c)
        category = category[0] if category else None
    except:
        category = None

    if category is None:
        context.status = 404
        raise ModuleError('Категория не найдена или не указана')

    if not permissions.check(context.user, 'create', ForumThread(category=category)):
        raise ModuleError('Недостаточно прав для создания темы')

    thread = ForumThread(category=category, name=title, description=description, author=context.user)
    thread.save()

    first_post = ForumPost(thread=thread, author=context.user, name=title)
    first_post.save()

    first_post_content = ForumPostVersion(post=first_post, source=source)
    first_post_content.save()

    return {'url': '/forum/t-%d/%s' % (thread.id, articles.normalize_article_name(title))}
