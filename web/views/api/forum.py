from django.http import HttpRequest

from renderer import single_pass_render
from renderer.parser import RenderContext
from renderer.utils import render_user_to_json
from web.controllers import forum_reactions
from web.models.forum import ForumPost, ForumPostVersion, ForumThread
from web.views.api import APIError, APIView


class ForumThreadView(APIView):
    @staticmethod
    def _check_access(request: HttpRequest, thread: ForumThread):
        if thread.article_id:
            if not request.user.has_perm('roles.view_article_comments', thread):
                raise APIError('Недостаточно прав', 403)
        elif (
            not request.user.has_perm('roles.view_forum_threads', thread) or
            not request.user.has_perm('roles.view_forum_posts', thread)
        ):
            raise APIError('Недостаточно прав', 403)

    @staticmethod
    def _get_latest_versions(posts: list[ForumPost]) -> dict[int, ForumPostVersion]:
        post_ids = [post.id for post in posts]
        if not post_ids:
            return {}

        q = ForumPostVersion.objects.filter(post_id__in=post_ids).order_by('post_id', '-created_at').distinct('post_id')
        return {version.post_id: version for version in q}

    def _render_post(
        self,
        request: HttpRequest,
        post: ForumPost,
        versions: dict[int, ForumPostVersion],
        children_by_parent: dict[int, list[ForumPost]],
        reaction_context: dict,
    ):
        version = versions.get(post.id)
        source = version.source if version else ''
        reaction_state = forum_reactions.serialize_post_reaction_state(post, request.user, reaction_context)

        return {
            'id': post.id,
            'name': post.name,
            'createdAt': post.created_at.isoformat(),
            'updatedAt': post.updated_at.isoformat(),
            'author': render_user_to_json(post.author),
            'replyTo': post.reply_to_id,
            'source': source,
            'content': single_pass_render(source, RenderContext(None, None, {}, request.user), 'message'),
            'version': {
                'createdAt': version.created_at.isoformat(),
                'author': render_user_to_json(version.author),
            } if version else None,
            'reactionState': reaction_state,
            'replies': [
                self._render_post(request, child, versions, children_by_parent, reaction_context)
                for child in children_by_parent.get(post.id, [])
            ],
        }

    def get(self, request: HttpRequest, forum_thread: int):
        thread = (
            ForumThread.objects
            .select_related('article', 'category', 'category__section', 'author')
            .prefetch_related(
                'article__authors',
                'author__roles',
                'author__roles__permissions',
                'author__roles__restrictions',
            )
            .filter(id=forum_thread)
            .first()
        )
        if thread is None:
            raise APIError('Тема не найдена', 404)

        self._check_access(request, thread)

        posts = list(
            ForumPost.objects
            .filter(thread=thread)
            .select_related('author')
            .prefetch_related(
                'author__roles',
                'author__roles__permissions',
                'author__roles__restrictions',
            )
            .order_by('created_at', 'id')
        )
        versions = self._get_latest_versions(posts)
        reaction_context = forum_reactions.build_reaction_context(posts, request.user)

        children_by_parent: dict[int, list[ForumPost]] = {}
        root_posts: list[ForumPost] = []
        post_ids = {post.id for post in posts}
        for post in posts:
            if post.reply_to_id and post.reply_to_id in post_ids:
                children_by_parent.setdefault(post.reply_to_id, []).append(post)
            else:
                root_posts.append(post)

        thread_name = thread.name if thread.category_id else thread.article.display_name
        return self.render_json(200, {
            'id': thread.id,
            'name': thread_name,
            'description': thread.description,
            'createdAt': thread.created_at.isoformat(),
            'updatedAt': thread.updated_at.isoformat(),
            'author': render_user_to_json(thread.author),
            'isPinned': thread.is_pinned,
            'isLocked': thread.is_locked,
            'article': {
                'uid': thread.article.id,
                'pageId': thread.article.full_name,
                'title': thread.article.title,
            } if thread.article_id else None,
            'category': {
                'id': thread.category.id,
                'name': thread.category.name,
                'section': {
                    'id': thread.category.section.id,
                    'name': thread.category.section.name,
                },
            } if thread.category_id else None,
            'postCount': len(posts),
            'availableReactions': reaction_context['availableReactions'],
            'reactionLimits': reaction_context['limits'],
            'posts': [
                self._render_post(request, post, versions, children_by_parent, reaction_context)
                for post in root_posts
            ],
        })
