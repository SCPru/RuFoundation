from django.conf import settings
from django.db import models
from .sites import SiteLimitedModel


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
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

        constraints = [models.UniqueConstraint(fields=['name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['name'])]

        permissions = [("add_article_in_category", "Может добавлять новые статьи в категорию"),
                       ("change_article_in_category", "Может изменять статьи в категории"),
                       ("delete_article_in_category", "Может удалять статьи в категории"),
                       ("can_vote_article_in_category", "Может голосовать за статьи в категории"),
                       ("can_lock_article_in_category", "Может заблокировать страницу для правок в категории")]

    name = models.TextField(verbose_name="Имя")

    def __str__(self) -> str:
        return self.name


class Article(SiteLimitedModel):
    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

        constraints = [models.UniqueConstraint(fields=['category', 'name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['category', 'name'])]

        permissions = [
            ("can_vote_article", "Может голосовать за статью"),
            ("can_lock_article", "Может заблокировать страницу для правок")
        ]

    category = models.TextField(default="_default", verbose_name="Категория")
    name = models.TextField(verbose_name="Имя")
    title = models.TextField(verbose_name="Заголовок")

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Родитель")
    tags = models.ManyToManyField(Tag, blank=True, related_name="articles", verbose_name="Тэги")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Автор")

    locked = models.BooleanField(default=False, verbose_name="Страница защищена")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

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

    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья")
    source = models.TextField(verbose_name="Исходник")
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
    rate = models.IntegerField(verbose_name="Оценка")

    def __str__(self) -> str:
        return f"{self.article}: {self.user} - {self.rate}"
