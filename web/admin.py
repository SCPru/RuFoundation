from guardian.admin import GuardedModelAdmin
from django.contrib import admin
from django import forms

from .models.articles import Article, ArticleVersion, ArticleLogEntry, Tag, Vote


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
class ArticleAdmin(GuardedModelAdmin):
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


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'rate']
    list_filter = ['article', 'user']

    exclude = ['article', 'user', 'rate']
    readonly_fields = ['article', 'user', 'rate']

    def has_add_permission(self, request):
        return False


@admin.register(ArticleVersion, ArticleLogEntry)
class BaseAdmin(admin.ModelAdmin):
    pass
