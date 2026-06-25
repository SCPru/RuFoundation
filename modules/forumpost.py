from modules import ModuleError
from renderer import RenderContext, single_pass_render

from datetime import datetime, timezone

from renderer.utils import render_user_to_json
from web.events import EventBase
from web.models import ForumPost, ForumPostVersion, User
from web.controllers import forum_reactions

from ._csrf_protection import csrf_safe_method


class OnForumEditPost(EventBase):
    user: User
    post: ForumPost
    title: str
    source: str
    prev_title: str
    prev_source: str


class OnForumDeletePost(EventBase):
    user: User
    post: ForumPost
    title: str
    source: str


def has_content():
    return False


def allow_api():
    return True


@csrf_safe_method
def api_fetch(context, params):
    post_id = params.get('postid', -1)

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not context.user.has_perm('roles.view_forum_posts', post):
        raise ModuleError('Недостаточно прав для просмотра сообщения')

    q = ForumPostVersion.objects.filter(post=post).order_by('-created_at')
    max_date = params.get('atdate')
    if max_date is not None:
        q = q.filter(created_at__lte=datetime.fromisoformat(max_date))

    version = q[:1]
    if not version:
        source = ''
    else:
        source = version[0].source

    content = single_pass_render(source, RenderContext(None, None, {}, context.user), 'message')

    return {
        'postId': post.id,
        'createdAt': post.created_at.isoformat(),
        'updatedAt': post.updated_at.isoformat(),
        'name': post.name,
        'source': source,
        'content': content
    }


def api_update(context, params):
    post_id = params.get('postid', -1)
    title = (params.get('name') or '').strip()
    source = (params.get('source') or '').strip()

    if not source:
        raise ModuleError('Не указан текст сообщения')

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not context.user.has_perm('roles.edit_forum_posts', post):
        raise ModuleError('Недостаточно прав для редактирования сообщения')

    latest_version = ForumPostVersion.objects.filter(post=post).order_by('-created_at').first()
    prev_source = latest_version.source if latest_version else ''

    if source != prev_source:
        new_version = ForumPostVersion(post=post, source=source, author=context.user)
        new_version.save()
        latest_version = new_version
        post.updated_at = datetime.now(timezone.utc)

    prev_title = post.name

    if title != post.name:
        post.name = title

    post.save()

    OnForumEditPost(context.user, post, title, source, prev_title, prev_source).emit()

    content = single_pass_render(source, RenderContext(None, None, {}, context.user), 'message')

    has_revisions = ForumPostVersion.objects.filter(post=post).count() > 1

    return {
        'postId': post.id,
        'name': post.name,
        'createdAt': post.created_at.isoformat(),
        'updatedAt': post.updated_at.isoformat(),
        'hasRevisions': has_revisions,
        'lastRevisionDate': post.updated_at.isoformat() if has_revisions else None,
        'lastRevisionAuthor': render_user_to_json(latest_version.author) if has_revisions and latest_version else None,
        'source': source,
        'content': content
    }


def api_delete(context, params):
    post_id = params.get('postid', -1)

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not context.user.has_perm('roles.delete_forum_posts', post):
        raise ModuleError('Недостаточно прав для удаления сообщения')
    
    latest_version = ForumPostVersion.objects.filter(post=post).order_by('-created_at').first()
    
    OnForumDeletePost(context.user, post, post.name, latest_version.source).emit()

    post.delete()

    return {
        'status': 'ok'
    }


@csrf_safe_method
def api_reactions(context, params):
    post_id = params.get('postid', -1)
    post = forum_reactions.get_forum_post_for_reactions(post_id)
    if post is None:
        raise ModuleError('Сообщение "%s" не существует' % post_id)
    if not forum_reactions.user_can_view_post(context.user, post):
        raise ModuleError('Недостаточно прав для просмотра сообщения')

    return forum_reactions.serialize_post_reaction_state(post, context.user)


def api_react(context, params):
    post_id = params.get('postid', -1)
    post = forum_reactions.get_forum_post_for_reactions(post_id, lock=True)
    if post is None:
        raise ModuleError('Сообщение "%s" не существует' % post_id)

    try:
        forum_reactions.add_reaction_to_post(post, params.get('reactionid'), context.user)
    except forum_reactions.ForumReactionError as e:
        raise ModuleError(e.message)

    return forum_reactions.serialize_post_reaction_state(post, context.user)


def api_unreact(context, params):
    post_id = params.get('postid', -1)
    post = forum_reactions.get_forum_post_for_reactions(post_id, lock=True)
    if post is None:
        raise ModuleError('Сообщение "%s" не существует' % post_id)

    try:
        forum_reactions.remove_reaction_from_post(
            post,
            params.get('reactionid'),
            context.user,
            params.get('userid'),
            params.get('allusers'),
        )
    except forum_reactions.ForumReactionError as e:
        raise ModuleError(e.message)

    return forum_reactions.serialize_post_reaction_state(post, context.user)


@csrf_safe_method
def api_fetchversions(context, params):
    post_id = params.get('postid', -1)

    post = ForumPost.objects.filter(id=post_id)
    if not post:
        raise ModuleError('Сообщение "%d" не существует', post_id)
    post = post[0]

    if not context.user.has_perm('roles.view_forum_posts', post):
        raise ModuleError('Недостаточно прав для просмотра сообщения')

    q = ForumPostVersion.objects.filter(post=post).order_by('-created_at')

    versions = []
    for version in q:
        versions.append({
            'createdAt': version.created_at.isoformat(),
            'author': render_user_to_json(version.author)
        })

    return {'versions': versions}
