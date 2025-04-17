from guardian.admin import GuardedModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib import admin
from django.urls import path
from solo.admin import SingletonModelAdmin
from django import forms

from .models.articles import *
from .models.forum import *
from .models.site import Site
from .models.users import User, VisualUserGroup
from .models.logs import ActionLogEntry
from .views.invite import InviteView
from .views.bot import CreateBotView
from .views.reset_votes import ResetUserVotesView
from .controllers import articles, logging


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
            'slug': forms.TextInput,
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
    fields = ['slug', 'title', 'headline', 'domain', 'media_domain']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and 'slug' in form.changed_data and form.cleaned_data.get('slug'):
            articles.change_slug_for_local_files(form.initial['slug'], form.cleaned_data['slug'])


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


class AdvancedUserChangeForm(UserChangeForm):
    class Meta:
        # fix username and wikidot_username input fields type
        widgets = {
            'username': forms.TextInput(attrs={'class': 'vTextField'}),
            'wikidot_username': forms.TextInput(attrs={'class': 'vTextField'})
        }


@admin.register(User)
class AdvancedUserAdmin(UserAdmin):
    form = AdvancedUserChangeForm

    list_filter = ['is_superuser', 'is_staff', 'is_editor', 'is_active', 'visual_group']
    list_display = ['username_or_wd', 'email']
    search_fields = ['username', 'wikidot_username', 'email']
    readonly_fields = ['api_key']

    fieldsets = UserAdmin.fieldsets
    fieldsets[2][1]['fields'] = ('is_active', 'inactive_until', 'is_forum_active', 'forum_inactive_until', 'is_editor', 'is_staff', 'is_superuser', 'visual_group', 'groups', 'user_permissions')
    fieldsets[1][1]['fields'] += ('bio', 'avatar')
    fieldsets[0][1]['fields'] = ('username', 'wikidot_username', 'type', 'password', 'api_key')

    inlines = []

    def get_urls(self):
        urls = super(AdvancedUserAdmin, self).get_urls()
        new_urls = [
            path('invite/', InviteView.as_view()),
            path('newbot/', CreateBotView.as_view()),
            path('<id>/activate/', InviteView.as_view()),
            path('<id>/reset_votes/', ResetUserVotesView.as_view()),
        ]
        return new_urls + urls

    def username_or_wd(self, obj):
        if obj.type == User.UserType.Wikidot:
            return 'wd:%s' % obj.wikidot_username
        return obj.username

    def get_form(self, request, *args, **kwargs):
        form = super().get_form(request, *args, **kwargs)
        not_required = ['inactive_until', 'forum_inactive_until', 'wikidot_username']
        for not_required_field in not_required:
            if not_required_field in form.base_fields:
                form.base_fields[not_required_field].required = False
        return form


class VisualUserGroupForm(forms.ModelForm):
    class Meta:
        model = VisualUserGroup
        widgets = {
            'name': forms.TextInput,
        }
        fields = '__all__'


@admin.register(VisualUserGroup)
class VisualUserGroupAdmin(GuardedModelAdmin):
    form = VisualUserGroupForm
    search_fields = ['name']
    fieldsets = (
        (None, {"fields": ('name', 'index')}),
    )


class ActionsLogForm(forms.ModelForm):
    class Meta:
        model = ActionLogEntry
        exclude = ['meta']


@admin.register(ActionLogEntry)
class ActionsLogAdmin(admin.ModelAdmin):
    form = ActionsLogForm
    list_filter = ['user', 'type', 'created_at', 'origin_ip']
    list_display = ['user_or_name', 'type', 'info', 'created_at', 'origin_ip']
    search_fields = ['meta']

    @admin.display(description=User.Meta.verbose_name)
    def user_or_name(self, obj):
        if obj.user == None:
            return f'{obj.stale_username} (удален)'
        return obj.user
    
    @admin.display(description='Подробности')
    def info(self, obj):
        return logging.get_action_log_entry_description(obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

