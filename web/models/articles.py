__all__ = [
    'TagsCategory',
    'Tag',
    'Category',
    'Article',
    'ArticleVersion',
    'ArticleLogEntry',
    'Vote',
    'ExternalLink'
]

import re
import auto_prefetch

from uuid import uuid4
from typing import Optional
from functools import cached_property

from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth import get_user_model

from web import threadvars
from web.fields import CITextField
from .roles import Role, PermissionsOverrideMixin, RolePermissionsOverrideMixin
from .settings import Settings
from .site import get_current_site


User = get_user_model()


class TagsCategorySlugValidator(RegexValidator):
    regex = r'^[a-zа-я0-9.-_]+\Z'
    message = 'Идентификатор категории тега может содержать только строчные буквы, цифры и символы [.-_] (без скобок).'
    flags = re.ASCII


class TagsCategory(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Категория тегов'
        verbose_name_plural = 'Категории тегов'

        constraints = [models.UniqueConstraint(fields=['slug'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['name'])]

    name = models.TextField('Полное название')
    description = models.TextField('Описание', blank=True)
    priority = models.PositiveIntegerField(null=True, blank=True, unique=True, verbose_name='Порядковый номер')
    slug = models.TextField('Идентификатор', unique=True, validators=[TagsCategorySlugValidator()])

    def __str__(self):
        return f'{self.name} ({self.slug})'

    @staticmethod
    def get_or_create_default_tags_category():
        category, _ = TagsCategory.objects.get_or_create(slug='_default', defaults=dict(name='Default'))
        return category.pk

    @property
    def is_default(self) -> bool:
        return self.slug == '_default'

    def save(self, *args, **kwargs):
        if not self.id and not self.name:
            self.name = self.slug
        return super(TagsCategory, self).save(*args, **kwargs)


class Tag(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

        constraints = [models.UniqueConstraint(fields=['category', 'name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['category', 'name'])]

    category = auto_prefetch.ForeignKey(TagsCategory, null=False, blank=False, on_delete=models.CASCADE, verbose_name='Категория', default=TagsCategory.get_or_create_default_tags_category)
    name = models.TextField('Название')

    def __str__(self):
        return self.full_name

    @property
    def full_name(self) -> str:
        if self.category and not self.category.is_default:
            return f'{self.category.slug}:{self.name}'
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super(Tag, self).save(*args, **kwargs)


class Category(auto_prefetch.Model, RolePermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Настройки категории'
        verbose_name_plural = 'Настройки категорий'

        constraints = [models.UniqueConstraint(fields=['name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['name'])]

    name = CITextField('Имя')

    is_indexed = models.BooleanField('Индексируется поисковиками', null=False, default=True)

    def __str__(self) -> str:
        return self.name
    
    def __eq__(self, value):
        if isinstance(value, str) and self.name == value:
            return True
        return super().__eq__(value)
    
    def __hash__(self):
        return super().__hash__()

    # this function returns site settings overridden by category settings.
    # if neither is set, falls back to defaults defined in Settings class.
    @cached_property
    def settings(self):
        category_settings = Settings.objects.filter(category=self).first()
        site_settings = get_current_site().settings
        return Settings.get_default_settings().merge(site_settings).merge(category_settings)
    
    @staticmethod
    def get_or_default_category(category):
        cat = Category.objects.filter(name=category)
        if not cat:
            return Category(name=category)
        else:
            return cat[0]


class Article(auto_prefetch.Model, PermissionsOverrideMixin):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

        constraints = [models.UniqueConstraint(fields=['category', 'name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['category']), models.Index(fields=['name']), models.Index(fields=['complete_full_name']), models.Index(fields=['created_at']), models.Index(fields=['updated_at'])]

    roles_override_pipeline = ['category_as_object']

    category = CITextField('Категория', default='_default')
    name = CITextField('Имя')
    complete_full_name = models.GeneratedField(
        expression=models.functions.Concat(
            'category', models.Value(':', output_field=CITextField()), 'name',
        ),
        output_field=CITextField(),
        db_persist=True
    )
    title = models.TextField('Заголовок')

    parent = auto_prefetch.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Родитель')
    tags = models.ManyToManyField(Tag, blank=True, related_name='articles', verbose_name='Тэги')
    author = auto_prefetch.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Автор')

    locked = models.BooleanField('Страница защищена', default=False)

    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    updated_at = models.DateTimeField('Время изменения', auto_now_add=True)

    media_name = models.TextField('Название папки с файлами в ФС-хранилище', unique=True, default=uuid4)

    @cached_property
    def settings(self):
        if self.category_as_object:
            return self.category_as_object.settings
        else:
            site_settings = get_current_site().settings
            return Settings.get_default_settings().merge(site_settings)

    @property
    def full_name(self) -> str:
        if self.category != '_default':
            return f'{self.category}:{self.name}'
        return self.name

    @property
    def display_name(self) -> str:
        return self.title.strip() or self.full_name
    
    @cached_property
    def category_as_object(self) -> Optional[Category]:
        return Category.objects.filter(name=self.category).first()

    def __str__(self) -> str:
        return f'{self.title} ({self.full_name})'
    
    def override_perms(self, user_obj, perms: set, roles=[]):
        if self.locked and 'roles.lock_articles' not in perms:
            lockable_perms = {'roles.edit_articles', 'roles.manage_articles_files', 'roles.tag_articles', 'roles.move_articles', 'roles.delete_articles'}
            perms = perms.difference(lockable_perms)
        return super().override_perms(user_obj, perms, roles)


class ArticleVersion(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Версия статьи'
        verbose_name_plural = 'Версии статей'

        indexes = [models.Index(fields=['article', 'created_at'])]

    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='Статья', related_name='versions')
    source = models.TextField('Исходник')
    ast = models.JSONField('AST-дерево статьи', blank=True, null=True)
    rendered = models.TextField('Рендер статьи', blank=True, null=True)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)

    def __str__(self) -> str:
        return f'{self.created_at.strftime('%Y-%m-%d, %H:%M:%S')} - {self.article}'


class ArticleLogEntry(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Запись в журнале изменений'
        verbose_name_plural = 'Записи в журнале изменений'

        constraints = [models.UniqueConstraint(fields=['article', 'rev_number'], name='%(app_label)s_%(class)s_unique')]

    class LogEntryType(models.TextChoices):
        Source = ('source', 'Изменение содержимого')
        Title = ('title', 'Изменение заголовка')
        Name = ('name', 'Изменение адреса страницы')
        Tags = ('tags', 'Изменение тегов')
        New = ('new', 'Создание страницы')
        Parent = ('parent', 'Изменение родителя')
        FileAdded = ('file_added', 'Добавление файлов')
        FileDeleted = ('file_deleted', 'Удаление файлов')
        FileRenamed = ('file_renamed', 'Переименование файлов')
        VotesDeleted = ('votes_deleted', 'Сброс рейтинга')
        Wikidot = ('wikidot', 'Правка с Wikidot')
        Revert = ('revert', 'Откат правки')

    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='Статья')
    user = auto_prefetch.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Пользователь')
    type = models.TextField('Тип', choices=LogEntryType.choices)
    meta = models.JSONField('Мета', default=dict, blank=True)
    created_at = models.DateTimeField('Время создания', auto_now_add=True)
    comment = models.TextField('Комментарий', blank=True)
    rev_number = models.PositiveIntegerField('Номер правки')

    def __str__(self) -> str:
        return f'№{self.rev_number} - {self.article}'


class Vote(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'

        constraints = [models.UniqueConstraint(fields=['article', 'user'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['article'])]

    article = auto_prefetch.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='Статья', related_name='votes')
    user = auto_prefetch.ForeignKey(User, null=True, on_delete=models.SET_NULL, verbose_name='Пользователь')
    rate = models.FloatField('Оценка')
    date = models.DateTimeField('Дата голоса', auto_now_add=True, null=True)
    role = auto_prefetch.ForeignKey(Role, on_delete=models.SET_NULL, verbose_name='Роль', null=True)

    def __str__(self) -> str:
        return f'{self.article}: {self.user} - {self.rate}'


class ExternalLink(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи'

        indexes = [
            models.Index(fields=['link_from', 'link_to']),
            models.Index(fields=['link_type'])
        ]

        constraints = [models.UniqueConstraint(fields=['link_from', 'link_to', 'link_type'], name='%(app_label)s_%(class)s_unique')]

    class Type(models.TextChoices):
        Include = 'include'
        Link = 'link'

    link_from = CITextField('Ссылающаяся статья', null=False)
    link_to = CITextField('Целевая статья', null=False)
    link_type = models.TextField('Тип ссылки', choices=Type.choices, null=False)
