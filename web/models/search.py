import re

from uuid import uuid4
from django.core.validators import RegexValidator
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver

from .articles import Article, ArticleVersion


class ArticleSearchIndex(models.Model):
    class Meta:
        verbose_name = "Индекс для поиска по статьям"
        verbose_name_plural = "Индексы для поиска по статьям"

        constraints = [models.UniqueConstraint(fields=['article'], name='%(app_label)s_%(class)s_unique')]
        indexes = [
            models.Index(fields=['article']),
            GinIndex(fields=['vector_plaintext_en']),
            GinIndex(fields=['vector_plaintext_ru']),
            GinIndex(fields=['vector_source_en']),
            GinIndex(fields=['vector_source_ru']),
            GinIndex(fields=['content_plaintext'], opclasses=['gin_trgm_ops'], name='article_search_plaintext_gin'),
            GinIndex(fields=['content_source'], opclasses=['gin_trgm_ops'], name='article_search_source_gin'),
        ]

    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, verbose_name="Статья")

    content_plaintext = models.TextField(verbose_name="Текст статьи")
    content_source = models.TextField(verbose_name="Исходный код статьи")

    vector_plaintext_en = SearchVectorField(null=True)
    vector_plaintext_ru = SearchVectorField(null=True)
    vector_source_en = SearchVectorField(null=True)
    vector_source_ru = SearchVectorField(null=True)

    def __str__(self):
        return f"Index ({str(self.article)})"


@receiver(post_save, sender=ArticleVersion)
def handle_post_save_version(sender, instance, **kwargs):
    update_search_index(instance)


def update_search_index(version: ArticleVersion):
    # this is imported here because this is too high-level for model code.
    # it starts doing import cycles on modules that don't exist yet
    from renderer import single_pass_render_text, RenderContext

    search_obj, created = ArticleSearchIndex.objects.get_or_create(article=version.article)
    context = RenderContext(article=version.article, source_article=version.article)
    search_obj.content_plaintext = single_pass_render_text(version.source, context, 'system')
    search_obj.content_source = version.source
    search_obj.vector_plaintext_en = (SearchVector('content_plaintext', config='english'))
    search_obj.vector_plaintext_ru = (SearchVector('content_plaintext', config='russian'))
    search_obj.vector_source_en = (SearchVector('content_source', config='english'))
    search_obj.vector_source_ru = (SearchVector('content_source', config='russian'))
    search_obj.save()
