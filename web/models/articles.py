from django.db import models


class Article(models.Model):
    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        constraints = [models.UniqueConstraint(fields=['category', 'name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['category', 'name'])]

    category = models.TextField(default="_default", verbose_name="Категория")
    name = models.TextField(verbose_name="Имя")
    title = models.TextField(verbose_name="Заголовок")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Родитель")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    @property
    def fullname(self) -> str:
        return f"{self.category}:{self.name}"

    def __str__(self) -> str:
        return f"{self.title} ({self.fullname})"


class ArticleVersion(models.Model):
    class Meta:
        verbose_name = "Версия статьи"
        verbose_name_plural = "Версии статей"
        indexes = [models.Index(fields=['article', 'created_at'])]

    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья")
    source = models.TextField(verbose_name="Исходник")
    rendered = models.TextField(blank=True, null=True, editable=False, verbose_name="Рендер статьи")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self) -> str:
        return f"{self.created_at.strftime('%Y-%m-%d, %H:%M:%S')} - {self.article}"


class ArticleLogEntry(models.Model):
    class Meta:
        verbose_name = "Запись статьи"
        verbose_name_plural = "Записи статей"
        constraints = [models.UniqueConstraint(fields=['article', 'rev_number'], name='%(app_label)s_%(class)s_unique')]

    class LogEntryType(models.TextChoices):
        Source = 'source'
        Title = 'title'
        Name = 'name'
        New = 'new'
        Parent = 'parent'

    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="Статья")
    type = models.TextField(choices=LogEntryType.choices, verbose_name="Тип")
    meta = models.JSONField(default=dict, editable=False, blank=True, verbose_name="Мета")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    rev_number = models.PositiveIntegerField(verbose_name="Номер правки")

    def __str__(self) -> str:
        return f"№{self.rev_number} - {self.article}"
