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

    type = models.TextField(choices=NotificationType.choices, verbose_name="Тип уведомлнения", blank=False, null=False)
    meta = models.JSONField(default=dict, verbose_name="Мета", blank=True, null=False)
    created_at = models.DateTimeField(verbose_name="Дата отправки", auto_now_add=True, blank=False, null=False)
    referred_to = models.TextField(verbose_name="Ведет к", blank=True, null=True)


class UserNotificationMapping(auto_prefetch.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    notification = models.ForeignKey(UserNotification, on_delete=models.CASCADE)
    is_viewed = models.BooleanField(blank=False, null=False, default=False)


class UserNotificationTemplate(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Шаблон уведомления"
        verbose_name_plural = "Шаблоны уведомлений"

    NOTIFICATION_DEFAULT_TEMPLATES = {
        'welcome': ('+++ Добро пожаловать', 'Рады видеть вас на сайте, %%recipient_name%%!'),
        'new_post_reply': ('+++ На ваш пост ответили', 'Ответ в ветке "%%thread_section%% >> %%thread_category%% >> %%thread_name%%":\n[[*user %%author_name%%]]\n**[[[%%link%%|%%reply_title%%]]]**\n%%reply_preview%%'),
        'new_thread_post': ('+++ Новый пост на форуме', 'Новый пост в ветке "%%thread_section%% >> %%thread_category%% >> %%thread_name%%":\n[[*user %%author_name%%]]\n**[[[%%link%%|%%post_title%%]]]**\n%%post_preview%%'),
        'new_article_revision': ('+++ Страница отредактирована', 'Страница [[[%%page_name%%|]]] была отредактирована:\n[[*user %%blame%%]]\nТип правки: %%rev_type%%\n[[ifexpr "%%comment%%"]]Комментарий: %%comment%%[[/ifexpr]]'),
    }

    COMMON_PARAMS = {
        'recipient_name': 'Имя получателя уведомления'
    }

    PARAM_MAPPING = {
        UserNotification.NotificationType.Welcome: {},
        UserNotification.NotificationType.NewPostReply: {
                'thread_section': 'Раздел форума',
                'thread_category': 'Категория форума',
                'thread_name': 'Название ветки',
                'author_name': 'Имя ответившего',
                'origin_title': 'Тема поста',
                'reply_title': 'Тема ответа',
                'reply_preview': 'Превью ответа',
                'link': 'Ссылка на пост',
            },
        UserNotification.NotificationType.NewThreadPost: {
                'thread_section': 'Раздел форума',
                'thread_category': 'Категория форума',
                'thread_name': 'Название ветки',
                'author_name': 'Имя автора поста',
                'post_title': 'Заголовок поста',
                'post_preview': 'Превью поста',
                'link': 'Ссылка на пост',
            },
        UserNotification.NotificationType.NewArticleRevision: {
                'page_name': 'Имя страницы',
                'blame': 'Автор правки',
                'rev_type': 'Тип правки',
                'comment': 'Комментарий',
            },
    }

    template_type = models.TextField(choices=UserNotification.NotificationType.choices, unique=True, verbose_name="Тип уведомлнения", blank=False, null=False)
    title = models.CharField(verbose_name='Заголовок', max_length=100, blank=False, null=False)
    message = models.TextField(verbose_name='Сообщение', blank=False, null=False)

    def __str__(self):
        return f"{self.template_type}: {self.title}"


class UserNotificationSubscription(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Подписка на уведомления"
        verbose_name_plural = "Подписки на уведомления"

    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Подписчик", blank=False, null=False)
    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья", blank=True, null=True)
    forum_thread = auto_prefetch.ForeignKey(ForumThread, on_delete=models.CASCADE, verbose_name="Ветка форума", blank=True, null=True)