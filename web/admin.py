from guardian.admin import GuardedModelAdmin
from django.contrib import admin
from django import forms

from .models.articles import *
from .models.forum import *
from .models.sites import Site


class TagsCategoryForm(forms.ModelForm):
    class Meta:
        model = TagsCategory
        widgets = {
            'name': forms.TextInput,
            'description': forms.TextInput,
            'slug': forms.TextInput,
        }
        fields = '__all__'


@admin.register(TagsCategory)
class TagsCategoryAdmin(admin.ModelAdmin):
    form = TagsCategoryForm
    list_filter = ['site__domain']
    list_display = ["name", "description", "priority", "slug"]


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
    list_filter = ['category', 'site__domain']
    list_display = ['name', 'category']


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
    fieldsets = (
        (None, {"fields": ('name', 'site')}),
        ('Права читателей',
         {"fields": ('readers_can_view', 'readers_can_create', 'readers_can_edit', 'readers_can_rate', 'readers_can_delete', 'readers_can_comment')}),
        ('Права участников', {"fields": ('users_can_view', 'users_can_create', 'users_can_edit', 'users_can_rate', 'users_can_delete', 'users_can_comment')})
    )
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


@admin.register(ForumSection)
class ForumSectionAdmin(admin.ModelAdmin):
    list_filter = ['site__domain']


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_filter = ['site__domain', 'section']
    list_display = ['name', 'section']