from django.conf import settings
from django.http import HttpRequest

from renderer import single_pass_render
from renderer.parser import RenderContext
from web.controllers.notifications import get_notifications, get_notification_templates, subscribe_to_notifications, unsubscribe_from_notifications
from web.models.articles import Article
from web.models.forum import ForumThread
from web.views.api import APIError, APIView, takes_json, takes_url_params


class NotificationsView(APIView):
    @staticmethod
    def _replace_params(text: str, params: dict):
        for param, value in params.items():
            text = text.replace(f'%%{param}%%', str(value))
        return text

    @takes_url_params
    def get(self, request: HttpRequest, *, cursor: int=-1, limit: int=10, unread: bool=False, mark_as_viewed: bool=False):
        render_context = RenderContext(None, None, {}, request.user)
        notification_templates = get_notification_templates()
        notifications = []

        notifications_batch = get_notifications(request.user, cursor=cursor, limit=limit, unread=unread, mark_as_viewed=mark_as_viewed)

        for notification, is_viewed in notifications_batch:
            template = notification_templates[notification.type]
            notifications.append({
                'id': notification.id,
                'title': single_pass_render(self._replace_params(template[0], notification.meta), render_context, mode='message'),
                'message': single_pass_render(self._replace_params(template[1], notification.meta), render_context, mode='message'),
                'created_at': notification.created_at.isoformat(),
                'referred_to': notification.referred_to,
                'is_viewed': is_viewed,
            })
        
        return self.render_json(
            200, {'cursor': notifications[-1]['id'] if notifications else -1, 'notifications': notifications}
        )


class NotificationsSubscribeView(APIView):
    @staticmethod
    def _get_subscription_info(data: dict):
        article_name = data.get('pageId')
        thread_id = data.get('forumThreadId')

        args = {}

        if article_name:
            args.update({'article': Article.objects.filter(name=article_name).first()})
        elif thread_id:
            args.update({'forum_thread': ForumThread.objects.filter(id=thread_id).first()})
        else:
            raise APIError('Некорректные параметры подписки', 400)

        return args

    @takes_json
    def post(self, request: HttpRequest, *args, **kwargs):
        args = self._get_subscription_info(self.json_input)
        subscription = subscribe_to_notifications(request.user, **args)

        if subscription:
            return self.render_json(200, {'status': 'ok'})
        else:
            raise APIError('Не удалось подписаться на уведомления', 400)
    
    @takes_json
    def delete(self, request: HttpRequest, *args, **kwargs):
        args = self._get_subscription_info(self.json_input)
        subscription = unsubscribe_from_notifications(request.user, **args)

        if subscription:
            return self.render_json(200, {'status': 'ok'})
        else:
            raise APIError('Такой подписки не существует', 404)
