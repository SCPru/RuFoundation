import auto_prefetch

from django.db import models
from django.contrib.auth import get_user_model

from web.models.articles import Article
from web.models.forum import ForumThread


User = get_user_model()

class UserNotification(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    POST_REPLY_TTL = 100
    POST_PREVIEW_MAX_SIZE = 150

    class NotificationType(models.TextChoices):
        Welcome = ("welcome", "Приветственное сообщение")
        NewPostReply = ("new_post_reply", "Ответ на пост")
        NewThreadPost = ("new_thread_post", "Новый пост")
        NewArticleRevision = ("new_article_revision", "Правка статьи")

    type = models.TextField(choices=NotificationType.choices, verbose_name="Тип уведомления", blank=False, null=False)
    meta = models.JSONField(default=dict, verbose_name="Мета", blank=True, null=False)
    created_at = models.DateTimeField(verbose_name="Дата отправки", auto_now_add=True, blank=False, null=False)
    referred_to = models.TextField(verbose_name="Ведет к", blank=True, null=True)


class UserNotificationMapping(auto_prefetch.Model):
    recipient = auto_prefetch.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    notification = auto_prefetch.ForeignKey(UserNotification, on_delete=models.CASCADE)
    is_viewed = models.BooleanField(blank=False, null=False, default=False)


class UserNotificationSubscription(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Подписка на уведомления"
        verbose_name_plural = "Подписки на уведомления"

    subscriber = auto_prefetch.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Подписчик", blank=False, null=False)
    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья", blank=True, null=True)
    forum_thread = auto_prefetch.ForeignKey(ForumThread, on_delete=models.CASCADE, verbose_name="Ветка форума", blank=True, null=True)