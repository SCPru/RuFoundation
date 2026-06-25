__all__ = [
    'ForumSection',
    'ForumCategory',
    'ForumThread',
    'ForumPost',
    'ForumPostVersion',
    'ForumReaction',
    'ForumPostReaction',
]

import auto_prefetch
import re
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Func, Value
from django.db.models.lookups import Exact
from django.contrib.auth import get_user_model

from web.models.roles import PermissionsOverrideMixin
from .articles import Article


User = get_user_model()


def validate_forum_reaction_image(file):
    extension = Path(file.name).suffix.lower()

    if extension == '.svg':
        max_svg_size = 1024 * 1024
        if getattr(file, 'size', 0) > max_svg_size:
            raise ValidationError('SVG-реакция должна быть не больше 1 МБ.')

        try:
            raw_svg = file.read(max_svg_size + 1)
            file.seek(0)
        except Exception:
            raise ValidationError('Невозможно прочитать SVG-файл.')

        if len(raw_svg) > max_svg_size:
            raise ValidationError('SVG-реакция должна быть не больше 1 МБ.')

        svg_source = raw_svg.decode('utf-8', errors='ignore').lower()

        if '<svg' not in svg_source:
            raise ValidationError('Файл не содержит SVG-разметку.')
        if re.search(r'<script\b|javascript:|\son\w+\s*=', svg_source):
            raise ValidationError('SVG-файл содержит потенциально опасный код.')
        return

    allowed_formats = {'PNG', 'JPEG', 'GIF', 'WEBP'}
    try:
        image = Image.open(file)
        image.verify()
        file.seek(0)
    except (UnidentifiedImageError, OSError):
        raise ValidationError('Загрузите изображение в формате PNG, JPEG, GIF, WebP или SVG.')

    if image.format not in allowed_formats:
        raise ValidationError('Загрузите изображение в формате PNG, JPEG, GIF, WebP или SVG.')


class ForumSection(auto_prefetch.Model, PermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Категория форума'
        verbose_name_plural = 'Категории форума'

    name = models.TextField('Название')
    description = models.TextField('Описание', blank=True)
    order = models.IntegerField('Порядок сортировки', default=0, blank=True)
    # this is hidden for anyone unless they click 'show hidden'
    is_hidden = models.BooleanField('Скрытая категория', default=False)
    # this is displayed for moderators and admins but completely hidden for users
    is_hidden_for_users = models.BooleanField('Видна только модераторам', default=False)

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

    name = models.TextField('Название')
    description = models.TextField('Описание', blank=True)
    order = models.IntegerField('Порядок сортировки', default=0, blank=True)
    section = auto_prefetch.ForeignKey(ForumSection, on_delete=models.DO_NOTHING, verbose_name='Категория')  # to-do: review later
    is_for_comments = models.BooleanField('Отображать комментарии к статьям в этом разделе', default=False)

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
            ),
            models.UniqueConstraint(fields=['article'], name='%(app_label)s_%(class)s_unique_article')
        ]

    roles_override_pipeline = ['article']

    name = models.TextField('Название')
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    updated_at = models.DateTimeField('Время изменения', auto_now_add=True)
    category = auto_prefetch.ForeignKey(ForumCategory, on_delete=models.DO_NOTHING, null=True, verbose_name='Раздел (если это тема)')  # to-do: review later
    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, null=True, verbose_name='Статья (если это комментарии)')
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    is_pinned = models.BooleanField('Пришпилено', default=False)
    is_locked = models.BooleanField('Закрыто', default=False)

    def override_perms(self, user_obj, perms: set, roles=[]):
        if user_obj == self.author:
            perms.add('roles.edit_forum_threads')
            perms.add('roles.pin_forum_posts')
        if self.article_id and not user_obj.is_anonymous and user_obj in self.article.authors.all():
            perms.add('roles.pin_forum_posts')
        if not user_obj.is_anonymous and not user_obj.is_forum_active or self.is_locked and 'roles.lock_forum_threads' not in perms:
            perms_to_revoke = {'roles.comment_articles', 'roles.create_forum_posts', 'roles.react_forum_posts', 'roles.edit_forum_posts', 'roles.delete_forum_posts', 'roles.edit_forum_threads', 'roles.pin_forum_threads', 'roles.pin_forum_posts', 'roles.move_forum_threads'}
            perms = perms.difference(perms_to_revoke)
        return super().override_perms(user_obj, perms, roles)


class ForumPost(auto_prefetch.Model, PermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Сообщение форума'
        verbose_name_plural = 'Сообщения форума'

    perms_override_pipeline = ['thread']

    name = models.TextField('Название', blank=True)
    created_at = models.DateTimeField('Время создания', auto_now_add=True, )
    updated_at = models.DateTimeField('Время изменения', auto_now_add=True)
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор')
    reply_to = auto_prefetch.ForeignKey('ForumPost', on_delete=models.SET_NULL, null=True, verbose_name='Ответ на комментарий')
    thread = auto_prefetch.ForeignKey(ForumThread, on_delete=models.CASCADE, verbose_name='Тема')
    is_pinned = models.BooleanField('Пришпилено', default=False, db_index=True)

    def override_perms(self, user_obj, perms: set, roles=[]):
        if user_obj == self.author and user_obj.has_perm('roles.create_forum_posts'):
            perms.add('roles.edit_forum_posts')
        return super().override_perms(user_obj, perms, roles)


class ForumPostVersion(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Версия сообщения форума'
        verbose_name_plural = 'Версии сообщений форума'

    post = auto_prefetch.ForeignKey(ForumPost, on_delete=models.CASCADE, verbose_name='Сообщение')
    source = models.TextField('Текст сообщения')
    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Автор правки')


class ForumReaction(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Реакция форума'
        verbose_name_plural = 'Реакции форума'
        ordering = ['sort_order', 'id']

        indexes = [
            models.Index(fields=['is_active', 'sort_order'], name='forum_react_active_order_idx'),
        ]

    name = models.TextField('Название')
    image = models.FileField('Картинка', upload_to='-/forum-reactions', validators=[validate_forum_reaction_image])
    is_active = models.BooleanField('Доступна', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0, editable=False, db_index=True)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)

    @property
    def image_url(self):
        if not self.image:
            return ''
        return '/local--files/%s' % self.image

    def __str__(self):
        return self.name


class ForumPostReaction(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Реакция на сообщение форума'
        verbose_name_plural = 'Реакции на сообщения форума'

        constraints = [
            models.UniqueConstraint(fields=['post', 'reaction', 'user'], name='%(app_label)s_%(class)s_unique'),
        ]
        indexes = [
            models.Index(fields=['post', 'reaction'], name='fpost_react_post_reaction_idx'),
            models.Index(fields=['user'], name='fpost_react_user_idx'),
        ]

    post = auto_prefetch.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='reactions', verbose_name='Сообщение')
    reaction = auto_prefetch.ForeignKey(ForumReaction, on_delete=models.CASCADE, related_name='post_reactions', verbose_name='Реакция')
    user = auto_prefetch.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_reactions', verbose_name='Пользователь')
    created_at = models.DateTimeField('Время создания', auto_now_add=True)

    def __str__(self):
        return '%s: %s -> %s' % (self.post_id, self.user, self.reaction)
