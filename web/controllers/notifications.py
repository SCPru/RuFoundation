from typing import Iterable

from django.contrib.auth.models import AbstractUser as _UserType

from web.models.forum import ForumThread
from web.models.notifications import UserNotification, UserNotificationMapping, UserNotificationSubscription
from web.models.articles import Article


def send_user_notification(recipients: _UserType | Iterable[_UserType], type: UserNotification.NotificationType, referred_to: str='', meta={}) -> UserNotification:
    notification = UserNotification(
        meta=meta,
        type=type,
        referred_to=referred_to,
    )

    notification.save()

    if isinstance(recipients, _UserType):
        recipients = (recipients,)

    UserNotificationMapping.objects.bulk_create([
        UserNotificationMapping(
            notification=notification,
            recipient=recipient,
            is_viewed=False
        ) for recipient in recipients]
    )
    
    return notification


def get_notification_subscribtions(article: Article=None, forum_thread: ForumThread=None) -> list[UserNotificationSubscription]:
    return UserNotificationSubscription.objects.filter(article=article, forum_thread=forum_thread)


def subscribe_to_notifications(subscriber: _UserType, article: Article=None, forum_thread: ForumThread=None) -> UserNotificationSubscription:
    if subscriber is None:
        return
    
    subscription = UserNotificationSubscription.objects.filter(subscriber=subscriber, article=article, forum_thread=forum_thread).first()

    if not subscription:
        if not (article or forum_thread):
            return None
        
        subscription = UserNotificationSubscription(
            subscriber=subscriber,
            article=article,
            forum_thread=forum_thread
        )
        subscription.save()

    return subscription


def unsubscribe_from_notifications(subscriber: _UserType, article: Article=None, forum_thread: ForumThread=None) -> bool:
    subscription = UserNotificationSubscription.objects.filter(subscriber=subscriber, article=article, forum_thread=forum_thread).first()

    if subscription:
        subscription.delete()
        return True
    return False


def is_subscribed(subscriber: _UserType, article: Article=None, forum_thread: ForumThread=None) -> bool:
    return UserNotificationSubscription.objects.filter(subscriber=subscriber, article=article, forum_thread=forum_thread).exists()


def get_notifications(user: _UserType, cursor=-1, limit=10, unread=True, mark_as_viewed=False) -> list[tuple[UserNotification, bool]]:
    related = UserNotificationMapping.objects.all().order_by('-notification_id')

    if not related:
        return []

    if cursor == -1:
        cursor = related.latest('notification_id').notification_id + 1

    related = related.filter(recipient=user, notification_id__lt=cursor)
    
    if unread:
        related = related.filter(is_viewed=False)

    result = [(n.notification, n.is_viewed) for n in related[:limit]]

    if mark_as_viewed:
        related.update(is_viewed=True)
        
    return result
