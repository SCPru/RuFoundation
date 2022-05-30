from django.db import models


class Article(models.Model):
    category = models.TextField()
    name = models.TextField()
    title = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def fullname(self) -> str:
        return f"{self.category}:{self.name}"

    def __str__(self) -> str:
        return self.fullname

    class Meta:
        constraints = [models.UniqueConstraint(fields=['category', 'name'], name='%(app_label)s_%(class)s_unique')]
        indexes = [models.Index(fields=['category', 'name'])]


class ArticleVersion(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    source = models.TextField()
    rendered = models.TextField(blank=True, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['article', 'created_at'])]


class ArticleLogEntry(models.Model):
    class LogEntryType(models.TextChoices):
        Source = 'source'
        Title = 'title'
        Name = 'name'
        New = 'new'
        Parent = 'parent'

    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    type = models.TextField(choices=LogEntryType.choices)
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(default='')
    rev_number = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['article', 'rev_number'], name='%(app_label)s_%(class)s_unique')]
