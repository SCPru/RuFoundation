from guardian.admin import GuardedModelAdmin
from django.contrib import admin
from django import forms

from .models.articles import *
from .models.sites import Site


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
    search_fields = ["name", "title"]
    list_filter = ['site__domain', 'category']


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        widgets = {
            'name': forms.TextInput,
        }
        fields = '__all__'


@admin.register(Category)
class CategoryAdmin(GuardedModelAdmin):
    form = CategoryForm
    list_filter = ['site__domain']


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
    list_filter = ['site__domain']


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['article', 'user', 'rate']
    list_filter = ['site__domain', 'article', 'user']

    exclude = ['article', 'user', 'rate']
    readonly_fields = ['article', 'user', 'rate']

    def has_add_permission(self, request):
        return False


class SiteForm(forms.ModelForm):
    class Meta:
        model = Article
        widgets = {
            'slug': forms.TextInput,
            'title': forms.TextInput,
            'headline': forms.TextInput,
            'domain': forms.TextInput,
            'media_domain': forms.TextInput
        }
        fields = '__all__'


@admin.register(Site)
class ArticleAdmin(GuardedModelAdmin):
    form = SiteForm


@admin.register(ArticleVersion, ArticleLogEntry)
class BaseAdmin(admin.ModelAdmin):
    list_filter = ['site__domain']


