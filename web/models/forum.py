from django.conf import settings
import auto_prefetch
from django.db import models
from django.db.models import Func, Value
from django.db.models.lookups import Exact
from django.contrib.auth import get_user_model

from web.models.roles import PermissionsOverrideMixin
from .articles import Article


__all__ = [
    'ForumSection',
    'ForumCategory',
    'ForumThread',
    'ForumPost',
    'ForumPostVersion'
]


User = get_user_model()


class ForumSection(auto_prefetch.Model, PermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Категория форума'
        verbose_name_plural = 'Категории форума'

    name = models.TextField(verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    order = models.IntegerField(verbose_name='Порядок сортировки', default=0, blank=True)
    # this is hidden for anyone unless they click 'show hidden'
    is_hidden = models.BooleanField(verbose_name='Скрытая категория', default=False)
    # this is displayed for moderators and admins but completely hidden for users
    is_hidden_for_users = models.BooleanField(verbose_name='Видна только модераторам', default=False)

    def __str__(self):
        return self.name
    
    def override_perms(self, user_obj, perms: set, roles=[]):
        if self.is_hidden_for_users and 'roles.view_forum_sections' in perms and 'roles.view_hidden_forum_sections' not in perms:
            perms.remove('roles.view_forum_sections')
        return super().override_perms(user_obj, perms, roles)


class ForumCategory(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Раздел форума'
        verbose_name_plural = 'Разделы форума'

    name = models.TextField(verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    order = models.IntegerField(verbose_name='Порядок сортировки', default=0, blank=True)
    section = auto_prefetch.ForeignKey(ForumSection, on_delete=models.DO_NOTHING, verbose_name='Категория')  # to-do: review later
    is_for_comments = models.BooleanField(verbose_name='Отображать комментарии к статьям в этом разделе', default=False)

    def __str__(self):
        return self.name


class ForumThread(auto_prefetch.Model, PermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Тема форума'
        verbose_name_plural = 'Темы форума'

        constraints = [
            # logic: a thread must have either 'article' or 'category' assigned
            # requires postgres >9.2
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_category_or_article',
                check=Exact(
                    lhs=Func('article_id', 'category_id', function='num_nonnulls', output_field=models.IntegerField()),
                    rhs=Value(1),
                ),
            )
        ]

    name = models.TextField(verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Время изменения')
    category = auto_prefetch.ForeignKey(ForumCategory, on_delete=models.DO_NOTHING, null=True, verbose_name='Раздел (если это тема)')  # to-do: review later
    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, null=True, verbose_name='Статья (если это комментарии)')
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    is_pinned = models.BooleanField(verbose_name='Пришпилено', default=False)
    is_locked = models.BooleanField(verbose_name='Закрыто', default=False)

    def override_perms(self, user_obj, perms: set, roles=[]):
        if user_obj == self.author:
            perms.add('roles.edit_forum_threads')
        if self.is_locked and 'roles.lock_forum_threads' not in perms:
            perms_to_revoke = {'roles.create_forum_posts', 'roles.edit_forum_posts', 'roles.delete_forum_posts', 'roles.edit_forum_threads', 'roles.pin_forum_threads', 'roles.move_forum_threads'}
            perms = perms.difference(perms_to_revoke)
        return super().override_perms(user_obj, perms, roles)


class ForumPost(auto_prefetch.Model, PermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Сообщение форума'
        verbose_name_plural = 'Сообщения форума'

    perms_override_pipeline = ['thread']

    name = models.TextField(verbose_name='Название', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Время изменения')
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    reply_to = auto_prefetch.ForeignKey('ForumPost', on_delete=models.SET_NULL, null=True, verbose_name='Ответ на комментарий')
    thread = auto_prefetch.ForeignKey(ForumThread, on_delete=models.CASCADE, verbose_name='Тема')

    def override_perms(self, user_obj, perms: set, roles=[]):
        if user_obj == self.author:
            perms.add('roles.edit_forum_posts')
        return super().override_perms(user_obj, perms, roles)


class ForumPostVersion(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Версия сообщения форума'
        verbose_name_plural = 'Версии сообщений форума'

    post = auto_prefetch.ForeignKey(ForumPost, on_delete=models.CASCADE, verbose_name='Сообщение')
    source = models.TextField(verbose_name='Текст сообщения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор правки')
