from django.contrib import admin

from .models.articles import Article, ArticleVersion, ArticleLogEntry


@admin.register(Article, ArticleVersion, ArticleLogEntry)
class BaseAdmin(admin.ModelAdmin):
    pass
