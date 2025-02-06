from guardian.admin import GuardedModelAdmin
from django.contrib import admin
from solo.admin import SingletonModelAdmin
from django import forms

from .models.articles import *
from .models.forum import *
from .models.site import Site

class TagsCategoryForm(forms.ModelForm):
    class Meta:
        model = TagsCategory
        widgets = {
            'name': forms.TextInput,
            'slug': forms.TextInput,
        }
        fields = ("name", "slug", "description", "priority")


@admin.register(TagsCategory)
class TagsCategoryAdmin(admin.ModelAdmin):
    form = TagsCategoryForm
    search_fields = ['name', 'slug', 'description']
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
    search_fields = ['name', 'category__name']
    list_filter = ['category']
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
    fieldsets = (
        (None, {"fields": ('name',)}),
        ('Права читателей',
         {"fields": ('readers_can_view', 'readers_can_create', 'readers_can_edit', 'readers_can_rate', 'readers_can_delete', 'readers_can_comment')}),
        ('Права участников', {"fields": ('users_can_view', 'users_can_create', 'users_can_edit', 'users_can_rate', 'users_can_delete', 'users_can_comment')})
    )
    inlines = [SettingsAdmin]


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        widgets = {
            'slug': forms.TextInput(attrs=dict(readonly=True, disabled=True)),
            'title': forms.TextInput,
            'headline': forms.TextInput,
            'domain': forms.TextInput,
            'media_domain': forms.TextInput
        }
        
        fields = '__all__'


@admin.register(Site)
class SiteAdmin(GuardedModelAdmin, SingletonModelAdmin):
    form = SiteForm
    inlines = [SettingsAdmin]

class ForumSectionForm(forms.ModelForm):
    class Meta:
        model = ForumSection
        widgets = {
            'name': forms.TextInput,
        }
        fields = '__all__'

@admin.register(ForumSection)
class ForumSectionAdmin(admin.ModelAdmin):
    form = ForumSectionForm
    search_fields = ['name', 'description']

class ForumCategoryForm(forms.ModelForm):
    class Meta:
        model = ForumCategory
        widgets = {
            'name': forms.TextInput,
        }
        fields = '__all__'

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    form = ForumCategoryForm
    search_fields = ['name', 'description']
    list_filter = ['section']
    list_display = ['name', 'section']