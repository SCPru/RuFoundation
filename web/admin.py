from solo.admin import SingletonModelAdmin
from adminsortable2.admin import SortableAdminMixin

from django.db.models.query import QuerySet
from django.db.models import ExpressionWrapper, F, Case, When, BooleanField
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.models import Permission
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib import admin
from django.urls import path
from django import forms

import web.fields
from web.views.sus_users import AdminSusActivityView

from .models import *
from .fields import CITextField
from .views.invite import InviteView
from .views.bot import CreateBotView
from .views.reset_votes import ResetUserVotesView
from .controllers import logging
from .permissions import get_role_permissions_content_type


class TagsCategoryForm(forms.ModelForm):
    class Meta:
        model = TagsCategory
        widgets = {
            'name': forms.TextInput,
            'slug': forms.TextInput,
        }
        fields = ('name', 'slug', 'description', 'priority')


@admin.register(TagsCategory)
class TagsCategoryAdmin(admin.ModelAdmin):
    form = TagsCategoryForm
    search_fields = ['name', 'slug', 'description']
    list_display = ['name', 'description', 'priority', 'slug']


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
        exclude = ['permissions_override']

    _add_override_roles_ = forms.ModelMultipleChoiceField(label='Добавить роли для переопределения', queryset=QuerySet(Role), required=False)
    _remove_override_roles_ = forms.ModelMultipleChoiceField(label='Удалить роли для переопределения', queryset=QuerySet(Role), required=False)
    _perms_override_ = web.fields.PermissionsOverrideField(exclude_admin=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        if instance:
            self.fields['_perms_override_'].widget.instance = instance

            overrided_roles = Role.objects.filter(rolepermissionsoverride__in=instance.permissions_override.all())
            self.fields['_add_override_roles_'].queryset = Role.objects.exclude(id__in=overrided_roles)
            self.fields['_remove_override_roles_'].queryset = overrided_roles
        else:
            self.fields['_perms_override_'].widget.instance = None
            self.fields['_add_override_roles_'].queryset = Role.objects.all()
            self.fields['_remove_override_roles_'].disabled = True


    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.save()

        roles_data = self.cleaned_data.get('_perms_override_', {})
        if roles_data:
            content_type = get_role_permissions_content_type()
            overrides = []

            instance.permissions_override.all().delete()

            for role_id, perms_data in roles_data.items():
                perms_override = RolePermissionsOverride.objects.create(role_id=role_id)

                if perms_data['allow']:
                    perms = Permission.objects.filter(codename__in=perms_data['allow'], content_type=content_type)
                    perms_override.permissions.set(perms)

                if perms_data['deny']:
                    restrictions = Permission.objects.filter(codename__in=perms_data['deny'], content_type=content_type)
                    perms_override.restrictions.set(restrictions)

                overrides.append(perms_override)

            instance.permissions_override.add(*overrides)

        roles_to_override = self.cleaned_data.get('_add_override_roles_', {})
        if roles_to_override:
            overrides = []
            for role in roles_to_override:
                overrides.append(RolePermissionsOverride.objects.create(role=role))

            instance.permissions_override.add(*overrides)

        roles_to_cancel_override = self.cleaned_data.get('_remove_override_roles_', {})
        if roles_to_cancel_override:
            instance.permissions_override.all().filter(role__in=roles_to_cancel_override).delete()

        if commit:
            instance.save()

        return instance


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    fieldsets = (
        (None, {
            'fields': ('name', 'is_indexed')
        }),
        ('Переопределение прав', {
            'fields': ('_add_override_roles_', '_remove_override_roles_', '_perms_override_')
        })
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
class SiteAdmin(SingletonModelAdmin):
    form = SiteForm
    inlines = [SettingsAdmin]
    fields = ['slug', 'title', 'headline', 'domain', 'media_domain']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'roles' in self.fields:
            self.fields['roles'].queryset = Role.objects.exclude(slug__in=['everyone', 'registered'])


@admin.register(User)
class AdvancedUserAdmin(ProtectsensitiveAdminMixin, UserAdmin):
    form = AdvancedUserChangeForm

    list_filter = ['is_superuser', 'is_active', 'roles']
    list_display = ['username_or_wd', 'email', 'is_active']
    search_fields = ['username', 'wikidot_username', 'email']
    readonly_fields = ['api_key', '_op_index']
    sensitive_fields = ['email']

    fieldsets = UserAdmin.fieldsets
    fieldsets[0][1]['fields'] = ('username', 'wikidot_username', 'type', 'password', 'api_key', '_op_index')
    fieldsets[1][1]['fields'] += ('bio', 'avatar')
    fieldsets[2][1]['fields'] = ('is_active', 'inactive_until', 'is_forum_active', 'forum_inactive_until', 'roles', 'is_superuser')

    @admin.display(ordering='username_or_wd')
    def username_or_wd(self, obj):
        return obj.__str__()
    
    @admin.display(description='Уровень привилегий')
    def _op_index(self, obj):
        return obj.operation_index

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path('invite/', InviteView.as_view()),
            path('newbot/', CreateBotView.as_view()),
            path('<id>/activate/', InviteView.as_view()),
            path('<id>/reset_votes/', ResetUserVotesView.as_view()),
        ]
        return new_urls + urls

    def get_form(self, request, *args, **kwargs):
        form = super().get_form(request, *args, **kwargs)
        not_required = ['inactive_until', 'forum_inactive_until', 'wikidot_username']
        for not_required_field in not_required:
            if not_required_field in form.base_fields:
                form.base_fields[not_required_field].required = False
        return form

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            readonly_fields += ['is_superuser']
        return readonly_fields
    
    def get_queryset(self, request):
        qs = super(AdvancedUserAdmin, self).get_queryset(request)
        return qs.annotate(
                username_or_wd=ExpressionWrapper(
                    Case(
                        When(type=User.UserType.Wikidot, then=F('wikidot_username')),
                        default=F('username'),
                        output_field=CITextField()
                    ),
                    output_field=CITextField()
                )
            ).order_by('username_or_wd')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'roles' and not request.user.has_perm('roles.manage_roles'):
            kwargs['disabled'] = True
        return super().formfield_for_manytomany(db_field, request, **kwargs)
    
    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and obj.operation_index <= request.user.operation_index:
            return False
        return super().has_change_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        if obj.pk:
            target = User.objects.get(id=obj.id)
            if change:
                if not request.user.is_superuser:
                    obj.is_superuser = target.is_superuser
                if not request.user.has_perm('roles.manage_roles'):
                    obj.roles.set(target.roles.all())
        super().save_model(request, obj, form, change)


class ActionsLogForm(forms.ModelForm):
    class Meta:
        model = ActionLogEntry
        exclude = ['meta']


@admin.register(ActionLogEntry)
class ActionsLogAdmin(ProtectsensitiveAdminMixin, admin.ModelAdmin):
    form = ActionsLogForm
    list_filter = ['user', 'type', 'created_at', 'origin_ip']
    list_display = ['user_or_name', 'type', 'info', 'created_at', 'origin_ip']
    search_fields = ['meta']
    sensitive_fields = ['origin_ip']

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
    
    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path('sus', AdminSusActivityView.as_view())
        ]
        return new_urls + urls


class RoleCategoryForm(forms.ModelForm):
    class Meta:
        model = RoleCategory
        fields = '__all__'


@admin.register(RoleCategory)
class RoleCategoryAdmin(admin.ModelAdmin):
    form = RoleCategoryForm


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        exclude = ['permissions', 'restrictions']

    _perms_ = web.fields.PermissionsField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        self.fields['_perms_'].widget.instance = instance

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.save()

        perms_data = self.cleaned_data.get('_perms_', {})
        if perms_data:
            content_type = get_role_permissions_content_type()

            instance.permissions.clear()
            instance.restrictions.clear()

            if perms_data['allow']:
                perms = Permission.objects.filter(codename__in=perms_data['allow'], content_type=content_type)
                instance.permissions.set(perms)

            if perms_data['deny']:
                restrictions = Permission.objects.filter(codename__in=perms_data['deny'], content_type=content_type)
                instance.restrictions.set(restrictions)

        if commit:
            instance.save()

        return instance


class IsVisualRoleFilter(SimpleListFilter):
    title = 'Визуальная роль'
    parameter_name = 'is_visual_role'

    def lookups(self, request, model_admin):
        return [
            (True, 'Да'),
            (False, 'Нет')
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.annotate(is_visual_role=ExpressionWrapper(
                F('group_votes') or \
                F('inline_visual_mode') != Role.InlineVisualMode.Hidden or \
                F('profile_visual_mode') != Role.ProfileVisualMode.Hidden,
                output_field=BooleanField()
            )).filter(is_visual_role=self.value())
        else:
            return queryset

@admin.register(Role)
class RoleAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = RoleForm
    list_filter = ['category', 'is_staff', IsVisualRoleFilter]
    list_display = ['__str__', '_users_number', '_idx']
    fieldsets = (
        (None, {
            'fields': ('slug', 'name', 'short_name', 'category', 'is_staff')
        }),
        ('Визуал', {
            'fields': ('group_votes', 'votes_title', 'inline_visual_mode', 'profile_visual_mode', 'color', 'icon', 'badge_text', 'badge_bg', 'badge_text_color', 'badge_show_border')
        }),
        ('Права доступа', {
            'fields': ('_perms_',)
        })
    )

    @admin.display(description='Индекс')
    def _idx(self, obj):
        return obj.index

    @admin.display(description='Пользователей')
    def _users_number(self, obj):
        if obj.slug in ['everyone', 'registered']:
            return User.objects.all().count()
        return obj.users.all().count()
    
    @property
    def change_list_template(self):
        return 'admin/%s/%s/change_list.html' % (self.opts.app_label, self.opts.model_name)
    
    @property
    def change_list_results_template(self):
        return 'admin/%s/%s/change_list_results.html' % (self.opts.app_label, self.opts.model_name)
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.slug  in ['everyone', 'registered']:
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser and obj.index < request.user.operation_index:
            return False
        return super().has_change_permission(request, obj)
        
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.slug  in ['everyone', 'registered']:
            return self.readonly_fields + ("slug",)
        return self.readonly_fields
    