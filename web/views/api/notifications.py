from django.http import HttpRequest

from renderer import single_pass_render
from renderer.parser import RenderContext
from web.controllers import articles, notifications
from web.models.forum import ForumThread
from web.models.notifications import UserNotification
from web.views.api import APIError, APIView, takes_json, takes_url_params


class NotificationsView(APIView):
    @staticmethod
    def _replace_params(text: str, params: dict):
        for param, value in params.items():
            text = text.replace(f'%%{param}%%', str(value))
        return text

    def render_notification(self, notification: UserNotification, is_viewed: bool, render_context: RenderContext):
        base_notification = dict(**{
            'id': notification.id,
            'type': notification.type,
            'created_at': notification.created_at.isoformat(),
            'referred_to': notification.referred_to,
            'is_viewed': is_viewed,
        }, **notification.meta)

        if notification.type in [UserNotification.NotificationType.NewThreadPost, UserNotification.NotificationType.NewPostReply]:
            base_notification['message'] = single_pass_render(base_notification['message_source'], render_context, mode='message'),

        return base_notification

    @takes_url_params
    def get(self, request: HttpRequest, *, cursor: int=-1, limit: int=10, unread: bool=False, mark_as_viewed: bool=False):
        render_context = RenderContext(None, None, {}, request.user)
        all_notifications = []

        notifications_batch = notifications.get_notifications(request.user, cursor=cursor, limit=limit, unread=unread, mark_as_viewed=mark_as_viewed)

        for notification, is_viewed in notifications_batch:
            all_notifications.append(self.render_notification(notification, is_viewed, render_context))
        
        return self.render_json(
            200, {'cursor': all_notifications[-1]['id'] if all_notifications else -1, 'notifications': all_notifications}
        )


class NotificationsSubscribeView(APIView):
    @staticmethod
    def _get_subscription_info(data: dict):
        article_name = data.get('pageId')
        thread_id = data.get('forumThreadId')

        args = {}

        if article_name:
            article = articles.get_article(article_name)
            args.update({'article': article})
        elif thread_id:
            args.update({'forum_thread': ForumThread.objects.filter(id=thread_id).first()})
        else:
            raise APIError('Некорректные параметры подписки', 400)

        return args
    
    @staticmethod
    def _verify_access(request: HttpRequest, args):
        if args.get('article') and not request.user.has_perm('roles.view_articles', args.get('article')):
            raise APIError('Недостаточно прав', 403)
        if args.get('forum_thread') and not request.user.has_perm('roles.view_forum_threads', args.get('forum_thread')):
            raise APIError('Недостаточно прав', 403)

    @takes_json
    def post(self, request: HttpRequest, *args, **kwargs):
        args = self._get_subscription_info(self.json_input)
        self._verify_access(request, args)
        subscription = notifications.subscribe_to_notifications(request.user, **args)

        if subscription:
            return self.render_json(200, {'status': 'ok'})
        else:
            raise APIError('Не удалось подписаться на уведомления', 400)
    
    @takes_json
    def delete(self, request: HttpRequest, *args, **kwargs):
        args = self._get_subscription_info(self.json_input)
        self._verify_access(request, args)
        subscription = notifications.unsubscribe_from_notifications(request.user, **args)

        if subscription:
            return self.render_json(200, {'status': 'ok'})
        else:
            raise APIError('Такой подписки не существует', 404)
