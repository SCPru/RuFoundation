from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import CITextField
from django.db import models
from .sites import SiteLimitedModel
from .settings import Settings


class Tag(SiteLimitedModel):
    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

        constraints = [models.UniqueConstraint(fields=['name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['name'])]

    name = models.TextField(verbose_name="Название", unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        return super(Tag, self).save(*args, **kwargs)


class Category(SiteLimitedModel):
    class Meta:
        verbose_name = "Настройки категории"
        verbose_name_plural = "Настройки категорий"

        constraints = [models.UniqueConstraint(fields=['name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['name'])]

    name = models.TextField(verbose_name="Имя")

    users_can_view = models.BooleanField(verbose_name='Пользователи могут просматривать статьи', null=False, default=True)
    users_can_create = models.BooleanField(verbose_name='Пользователи могут создавать статьи', null=False, default=True)
    users_can_edit = models.BooleanField(verbose_name='Пользователи могут редактировать статьи', null=False, default=True)
    users_can_rate = models.BooleanField(verbose_name='Пользователи могут голосовать за статьи', null=False, default=True)
    users_can_comment = models.BooleanField(verbose_name='Пользователи могут комментировать статьи', null=False, default=True)
    users_can_delete = models.BooleanField(verbose_name='Пользователи могут удалять статьи', null=False, default=False)

    def __str__(self) -> str:
        return self.name

    # this function returns site settings overridden by category settings.
    # if neither is set, falls back to defaults defined in Settings class.
    def get_settings(self):
        category_settings = Settings.objects.filter(category=self).first() or Settings.get_default_settings()
        site_settings = Settings.objects.filter(site=self.site).first() or Settings.get_default_settings()
        return Settings.get_default_settings().merge(site_settings).merge(category_settings)


class Article(SiteLimitedModel):
    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

        constraints = [models.UniqueConstraint(fields=['category', 'name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['category', 'name'])]

    category = models.TextField(default="_default", verbose_name="Категория")
    name = models.TextField(verbose_name="Имя")
    title = models.TextField(verbose_name="Заголовок")

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Родитель")
    tags = models.ManyToManyField(Tag, blank=True, related_name="articles", verbose_name="Тэги")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Автор")

    locked = models.BooleanField(default=False, verbose_name="Страница защищена")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    media_name = models.TextField(verbose_name="Название папки с файлами в ФС-хранилище", unique=True, default=uuid4)

    def get_settings(self):
        try:
            category_as_object = Category.objects.get(name__iexact=self.category)
            return category_as_object.get_settings()
        except Category.DoesNotExist:
            return Settings.get_default_settings().merge(self.site.get_settings())

    @property
    def full_name(self) -> str:
        if self.category != '_default':
            return f"{self.category}:{self.name}"
        return self.name

    def __str__(self) -> str:
        return f"{self.title} ({self.full_name})"


class ArticleVersion(SiteLimitedModel):
    class Meta:
        verbose_name = "Версия статьи"
        verbose_name_plural = "Версии статей"

        indexes = [models.Index(fields=['article', 'created_at'])]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья", related_name='versions')
    source = models.TextField(verbose_name="Исходник")
    ast = models.JSONField(blank=True, null=True, verbose_name="AST-дерево статьи")
    rendered = models.TextField(blank=True, null=True, verbose_name="Рендер статьи")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self) -> str:
        return f"{self.created_at.strftime('%Y-%m-%d, %H:%M:%S')} - {self.article}"


class ArticleLogEntry(SiteLimitedModel):
    class Meta:
        verbose_name = "Запись в журнале изменений"
        verbose_name_plural = "Записи в журнале изменений"

        constraints = [models.UniqueConstraint(fields=['article', 'rev_number'], name='%(app_label)s_%(class)s_unique')]

    class LogEntryType(models.TextChoices):
        Source = 'source'
        Title = 'title'
        Name = 'name'
        Tags = 'tags'
        New = 'new'
        Parent = 'parent'
        FileAdded = 'file_added'
        FileDeleted = 'file_deleted'
        FileRenamed = 'file_renamed'
        Wikidot = 'wikidot'

    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Пользователь")
    type = models.TextField(choices=LogEntryType.choices, verbose_name="Тип")
    meta = models.JSONField(default=dict, blank=True, verbose_name="Мета")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    rev_number = models.PositiveIntegerField(verbose_name="Номер правки")

    def __str__(self) -> str:
        return f"№{self.rev_number} - {self.article}"


class Vote(SiteLimitedModel):
    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

        constraints = [models.UniqueConstraint(fields=['article', 'user'], name='%(app_label)s_%(class)s_unique')]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья", related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, verbose_name="Пользователь")
    rate = models.FloatField(verbose_name="Оценка")

    def __str__(self) -> str:
        return f"{self.article}: {self.user} - {self.rate}"


class ExternalLink(SiteLimitedModel):
    class Meta:
        verbose_name = "Связь"
        verbose_name_plural = "Связи"

        constraints = [models.UniqueConstraint(fields=['link_from', 'link_to', 'link_type'], name='%(app_label)s_%(class)s_unique')]

    class Type(models.TextChoices):
        Include = 'include'
        Link = 'link'

    link_from = CITextField(verbose_name="Ссылающаяся статья", null=False)
    link_to = CITextField(verbose_name="Целевая статья", null=False)
    link_type = models.TextField(choices=Type.choices, verbose_name="Тип ссылки", null=False)
