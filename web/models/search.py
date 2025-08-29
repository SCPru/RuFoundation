import auto_prefetch
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.db.models.functions import Upper

from .articles import Article


class ArticleSearchIndex(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Индекс для поиска по статьям"
        verbose_name_plural = "Индексы для поиска по статьям"

        constraints = [models.UniqueConstraint(fields=['article'], name='%(app_label)s_%(class)s_unique')]
        indexes = [
            models.Index(fields=['article']),
            GinIndex(fields=['vector_plaintext']),
            GinIndex(fields=['content_plaintext'], opclasses=['gin_trgm_ops'], name='article_search_plaintext_gin'),
            GinIndex(fields=['content_source'], opclasses=['gin_trgm_ops'], name='article_search_source_gin'),
            GinIndex(
                OpClass(Upper('content_source'), name='gin_trgm_ops'),
                name='content_source_lower_trgm_gin'
            ),
        ]

    article = auto_prefetch.ForeignKey(Article, on_delete=models.SET_NULL, null=True, verbose_name="Статья")

    content_plaintext = models.TextField(verbose_name="Текст статьи")
    content_source = models.TextField(verbose_name="Исходный код статьи")

    vector_plaintext = SearchVectorField(null=True)

    def __str__(self):
        return f"Index ({str(self.article)})"
