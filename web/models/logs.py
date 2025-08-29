import auto_prefetch
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

class ActionLogEntry(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Действие'
        verbose_name_plural = 'Действия'

    class ActionType(models.TextChoices):
        Vote = ('vote', 'Оценка')
        NewArticle = ('create_article', 'Страница создана')
        EditArticle = ('edit_article', 'Страница отредактирована')
        RemoveArticle = ('remove_article', 'Страница удалена')
        NewForumPost = ('add_forum_post', 'Новое сообщение форума')
        EditForumPost = ('edit_forum_post', 'Сообщение форума изменено')
        RemoveForumPost = ('remove_forum_post', 'Сообщение форума удалено')
        ChangeProfileInfo = ('change_profile_info', 'Информация профиля изменена')

    user = auto_prefetch.ForeignKey(User, verbose_name='Пользователь', on_delete=models.DO_NOTHING)
    stale_username = models.TextField(verbose_name='Имя на момент действия')
    type = models.TextField(choices=ActionType.choices, verbose_name='Тип')
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время')
    origin_ip = models.GenericIPAddressField(verbose_name='IP Адрес', blank=True, null=True)