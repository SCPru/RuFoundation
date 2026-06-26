from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError
from django.db.models import Count

from renderer.utils import render_user_to_json
from web.events import EventBase
from web.models.forum import ForumPost, ForumPostReaction, ForumReaction
from web.models.settings import Settings
from web.models.site import get_current_site
from web.types import _UserType


class OnForumReactionAdd(EventBase):
    user: _UserType
    post: ForumPost
    reaction: ForumReaction


class OnForumReactionRemove(EventBase):
    user: _UserType
    target_user: _UserType
    post: ForumPost
    reaction: ForumReaction


class ForumReactionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def get_forum_reaction_limits():
    site = get_current_site(required=False)
    settings = site.settings if site else Settings.get_default_settings()
    return {
        'maxPerUser': max(0, settings.forum_reactions_per_user or 0),
        'maxPerPost': max(0, settings.forum_reaction_types_per_post or 0),
    }


def get_forum_post_for_reactions(post_id, lock=False):
    try:
        post_id = int(post_id)
    except (TypeError, ValueError):
        return None

    q = ForumPost.objects.select_related('thread', 'thread__article', 'thread__category')
    if lock:
        q = q.select_for_update(of=('self',))
    return q.filter(id=post_id).first()


def user_can_view_post(user: _UserType, post: ForumPost) -> bool:
    if post.thread.article_id:
        return user.has_perm('roles.view_article_comments', post.thread)
    return (
        user.has_perm('roles.view_forum_threads', post.thread) and
        user.has_perm('roles.view_forum_posts', post)
    )


def user_has_reaction_permission(user: _UserType, post: ForumPost) -> bool:
    if user is None or isinstance(user, AnonymousUser) or user.is_anonymous:
        return False
    if not user.is_active or not user.is_forum_active:
        return False
    if not user_can_view_post(user, post):
        return False

    return user.has_perm('roles.react_forum_posts', post)


def user_can_add_reaction(user: _UserType, post: ForumPost) -> bool:
    if not user_has_reaction_permission(user, post):
        return False

    limits = get_forum_reaction_limits()
    if limits['maxPerUser'] <= 0 or limits['maxPerPost'] <= 0:
        return False
    return True


def user_can_react(user: _UserType) -> bool:
    if user is None or isinstance(user, AnonymousUser) or user.is_anonymous:
        return False
    return user.is_active and user.is_forum_active and user.has_perm('roles.react_forum_posts')


def user_can_moderate_reactions(user: _UserType, post: ForumPost) -> bool:
    if user is None or isinstance(user, AnonymousUser) or user.is_anonymous:
        return False
    return user.has_perm('roles.delete_forum_posts', post)


def user_can_manage_reactions(user: _UserType) -> bool:
    if user is None or isinstance(user, AnonymousUser) or user.is_anonymous:
        return False
    return (
        user.has_perm('roles.manage_forum_reactions') or
        user.has_perm('web.change_forumreaction')
    )


def serialize_reaction(reaction: ForumReaction):
    return {
        'id': reaction.id,
        'name': reaction.name,
        'imageUrl': reaction.image_url,
        'isActive': reaction.is_active,
    }


def serialize_available_reactions(viewer: _UserType=None):
    reactions = ForumReaction.objects.all()
    if not user_can_manage_reactions(viewer):
        reactions = reactions.filter(is_active=True)

    return [
        serialize_reaction(reaction)
        for reaction in reactions.order_by('sort_order', 'id')
    ]


def serialize_post_reactions(posts, viewer: _UserType):
    posts = list(posts)
    post_ids = [post.id for post in posts]
    if not post_ids:
        return {}

    viewer_id = None if viewer is None or isinstance(viewer, AnonymousUser) else viewer.id
    reactions = (
        ForumPostReaction.objects
        .filter(post_id__in=post_ids)
        .select_related('reaction', 'user')
        .prefetch_related('user__roles')
        .order_by('created_at', 'id')
    )

    by_post = {post_id: [] for post_id in post_ids}
    summaries = {}

    for post_reaction in reactions:
        key = (post_reaction.post_id, post_reaction.reaction_id)
        summary = summaries.get(key)
        if summary is None:
            summary = {
                'reaction': serialize_reaction(post_reaction.reaction),
                'count': 0,
                'me': False,
                'users': [],
            }
            summaries[key] = summary
            by_post[post_reaction.post_id].append(summary)

        summary['count'] += 1
        summary['me'] = summary['me'] or post_reaction.user_id == viewer_id
        summary['users'].append(render_user_to_json(post_reaction.user, skip_perms=True))

    for post_summaries in by_post.values():
        post_summaries.sort(key=lambda summary: -summary['count'])

    return by_post


def build_reaction_context(posts, viewer: _UserType):
    posts = list(posts)
    return {
        'availableReactions': serialize_available_reactions(viewer),
        'limits': get_forum_reaction_limits(),
        'byPost': serialize_post_reactions(posts, viewer),
    }


def serialize_post_reaction_state(post: ForumPost, viewer: _UserType, reaction_context=None):
    if reaction_context is None:
        reaction_context = build_reaction_context([post], viewer)

    reactions = reaction_context['byPost'].get(post.id, [])
    return {
        'availableReactions': reaction_context['availableReactions'],
        'limits': reaction_context['limits'],
        'reactions': reactions,
        'totalCount': sum(reaction['count'] for reaction in reactions),
        'myCount': sum(1 for reaction in reactions if reaction['me']),
        'canReact': user_can_add_reaction(viewer, post),
        'canRemoveOwnReactions': user_has_reaction_permission(viewer, post) or user_can_moderate_reactions(viewer, post),
        'canModerateReactions': user_can_moderate_reactions(viewer, post),
        'canUseInactiveReactions': user_can_manage_reactions(viewer),
    }


def _is_truthy(value):
    return value is True or str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def add_reaction_to_post(post: ForumPost, reaction_id, user):
    if not user_can_add_reaction(user, post):
        raise ForumReactionError('Недостаточно прав для добавления реакции')

    try:
        reaction_id = int(reaction_id)
    except (TypeError, ValueError):
        raise ForumReactionError('Некорректная реакция')

    reaction = ForumReaction.objects.filter(id=reaction_id).first()
    if reaction is None:
        raise ForumReactionError('Реакция не найдена')
    if not reaction.is_active and not user_can_manage_reactions(user):
        raise ForumReactionError('Эта реакция сейчас недоступна')

    if ForumPostReaction.objects.filter(post=post, reaction=reaction, user=user).exists():
        return

    limits = get_forum_reaction_limits()
    user_reactions_count = ForumPostReaction.objects.filter(post=post, user=user).count()
    if user_reactions_count >= limits['maxPerUser']:
        raise ForumReactionError('Достигнут лимит реакций пользователя под этим сообщением')

    reaction_type_exists = ForumPostReaction.objects.filter(post=post, reaction=reaction).exists()
    if not reaction_type_exists:
        post_reaction_types_count = ForumPostReaction.objects.filter(post=post).values('reaction_id').distinct().count()
        if post_reaction_types_count >= limits['maxPerPost']:
            raise ForumReactionError('Достигнут лимит типов реакций под этим сообщением')

    try:
        ForumPostReaction.objects.create(post=post, reaction=reaction, user=user)
    except IntegrityError:
        return

    OnForumReactionAdd(user, post, reaction).emit()


def remove_reaction_from_post(post: ForumPost, reaction_id, actor, user_id=None, all_users=False):
    if actor is None or isinstance(actor, AnonymousUser) or actor.is_anonymous:
        raise ForumReactionError('Войдите, чтобы удалить реакцию')
    if not user_can_view_post(actor, post):
        raise ForumReactionError('Недостаточно прав для просмотра сообщения')

    try:
        reaction_id = int(reaction_id)
    except (TypeError, ValueError):
        raise ForumReactionError('Некорректная реакция')

    can_moderate = user_can_moderate_reactions(actor, post)
    if _is_truthy(all_users):
        if not can_moderate:
            raise ForumReactionError('Недостаточно прав для удаления реакции')

        post_reactions = list(
            ForumPostReaction.objects
            .filter(post=post, reaction_id=reaction_id)
            .select_related('reaction', 'user')
        )
        for post_reaction in post_reactions:
            reaction = post_reaction.reaction
            target_user = post_reaction.user
            post_reaction.delete()
            OnForumReactionRemove(actor, target_user, post, reaction).emit()
        return

    target_user_id = actor.id
    if user_id is not None:
        try:
            target_user_id = int(user_id)
        except (TypeError, ValueError):
            raise ForumReactionError('Некорректный пользователь')

    if target_user_id != actor.id and not can_moderate:
        raise ForumReactionError('Недостаточно прав для удаления чужой реакции')
    if target_user_id == actor.id and not can_moderate and not user_has_reaction_permission(actor, post):
        raise ForumReactionError('Недостаточно прав для удаления реакции')

    post_reaction = (
        ForumPostReaction.objects
        .filter(post=post, reaction_id=reaction_id, user_id=target_user_id)
        .select_related('reaction', 'user')
        .first()
    )
    if post_reaction is None:
        return

    reaction = post_reaction.reaction
    target_user = post_reaction.user
    post_reaction.delete()
    OnForumReactionRemove(actor, target_user, post, reaction).emit()
