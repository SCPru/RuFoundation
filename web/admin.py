from guardian.admin import GuardedModelAdmin
from django.contrib import admin
from django import forms

from .models.articles import *
from .models.files import File
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


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        widgets = {
            'rating_mode': forms.Select
        }
        fields = '__all__'
        exclude = ['site', 'category']


class SettingsAdmin(admin.StackedInline):
    form = SettingsForm
    model = Settings
    can_delete = False
    max_num = 1


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
    inlines = [SettingsAdmin]


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        widgets = {
            'slug': forms.TextInput,
            'title': forms.TextInput,
            'headline': forms.TextInput,
            'domain': forms.TextInput,
            'media_domain': forms.TextInput
        }
        fields = '__all__'


@admin.register(Site)
class SiteAdmin(GuardedModelAdmin):
    form = SiteForm
    inlines = [SettingsAdmin]


@admin.register(ArticleVersion, ArticleLogEntry, File)
class BaseAdmin(admin.ModelAdmin):
    list_filter = ['site__domain']


