from django.contrib import admin
from django import forms

from .models.articles import Article, ArticleVersion, ArticleLogEntry, Tag


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        widgets = {
            'category': forms.TextInput,
            'name': forms.TextInput,
            'title': forms.TextInput
        }
        fields = '__all__'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleForm


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        widgets = {
            'name': forms.TextInput
        }
        fields = '__all__'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    form = TagForm


@admin.register(ArticleVersion, ArticleLogEntry)
class BaseAdmin(admin.ModelAdmin):
    pass
