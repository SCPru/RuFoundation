from modules import ModuleError
from renderer import RenderContext, single_pass_render

from datetime import datetime

from renderer.utils import render_user_to_json
from web.controllers import permissions
from web.models.forum import ForumPost, ForumPostVersion


def has_content():
    return False


def allow_api():
    return True


def api_fetch(context, params):
    post_id = params.get('postId', -1)

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not permissions.check(context.user, 'view', post):
        raise ModuleError('Недостаточно прав для просмотра сообщения')

    q = ForumPostVersion.objects.filter(post=post).order_by('-created_at')
    max_date = params.get('atDate')
    if max_date is not None:
        q = q.filter(created_at__lte=datetime.fromisoformat(max_date))

    version = q[:1]
    if not version:
        source = ''
    else:
        source = version[0].source

    content = single_pass_render(source, RenderContext(None, None, {}, context.user))

    return {
        'postId': post.id,
        'createdAt': post.created_at.isoformat(),
        'updatedAt': post.updated_at.isoformat(),
        'name': post.name,
        'source': source,
        'content': content
    }


def api_update(context, params):
    post_id = params.get('postId', -1)
    title = (params.get('name') or '').strip()
    source = (params.get('source') or '').strip()

    if not source:
        raise ModuleError('Не указан текст сообщения')

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not permissions.check(context.user, 'edit', post):
        raise ModuleError('Недостаточно прав для редактирования сообщения')

    latest_version = ForumPostVersion.objects.filter(post=post).order_by('-created_at')[:1]
    prev_source = latest_version[0].source if latest_version else ''

    if source != prev_source:
        new_version = ForumPostVersion(post=post, source=source, author=context.user)
        new_version.save()

    if title != post.name:
        post.name = title

    post.updated_at = datetime.now()
    post.save()

    content = single_pass_render(source, RenderContext(None, None, {}, context.user))

    return {
        'postId': post.id,
        'name': post.name,
        'createdAt': post.created_at.isoformat(),
        'updatedAt': post.updated_at.isoformat(),
        'source': source,
        'content': content
    }


def api_delete(context, params):
    post_id = params.get('postId', -1)

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not permissions.check(context.user, 'delete', post):
        raise ModuleError('Недостаточно прав для удаления сообщения')

    post.delete()

    return {
        'status': 'ok'
    }


def api_fetchversions(context, params):
    post_id = params.get('postId', -1)

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not permissions.check(context.user, 'view', post):
        raise ModuleError('Недостаточно прав для просмотра сообщения')

    q = ForumPostVersion.objects.filter(post=post).order_by('-created_at')

    versions = []
    for version in q:
        versions.append({
            'createdAt': version.created_at.isoformat(),
            'author': render_user_to_json(version.author)
        })

    return {'versions': versions}
