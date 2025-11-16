from web.permissions import BaseRolePermission


def is_perms_collection():
    return True


class ManageUsersPermission(BaseRolePermission):
    name = 'Управлять пользователями'
    codename = 'manage_users'
    description = 'Позволяет создавать и редактировать пользователей'
    represent_django_perms = ['web.view_user', 'web.add_user', 'web.change_user']
    group = 'Админка'
    admin_only = True


class ManageRolesPermission(BaseRolePermission):
    name = 'Управлять ролями'
    codename = 'manage_roles'
    description = 'Позволяет создавать, редактировать и удалять роли и категории ролей'
    represent_django_perms = ['web.view_role', 'web.add_role', 'web.change_role', 'web.delete_role', 'web.view_rolecategory', 'web.add_rolecategory', 'web.change_rolecategory', 'web.delete_rolecategory']
    group = 'Админка'
    admin_only = True


class ManageSitePermission(BaseRolePermission):
    name = 'Управлять сайтом'
    codename = 'manage_site'
    description = 'Позволяет изменять основные параметры сайта'
    represent_django_perms = ['web.view_site', 'web.change_site']
    group = 'Админка'
    admin_only = True


class ViewActionsLogPermission(BaseRolePermission):
    name = 'Просматривать события'
    codename = 'view_actions_log'
    description = 'Позволяет просматривать журнал событий'
    represent_django_perms = ['web.view_actionlogentry']
    group = 'Админка'
    admin_only = True
    

class ManageCaregoriesPermission(BaseRolePermission):
    name = 'Управлять категориями'
    codename = 'manage_categories'
    description = 'Позволяет создавать, редактировать и удалять категории статей'
    represent_django_perms = ['web.view_category', 'web.add_category', 'web.change_category', 'web.delete_category']
    group = 'Админка'
    admin_only = True


class ManageTagsPermission(BaseRolePermission):
    name = 'Управлять тегами'
    codename = 'manage_tags'
    description = 'Позволяет создавать, редактировать и удалять теги и категории тегов'
    represent_django_perms = ['web.view_tag', 'web.add_tag', 'web.change_tag', 'web.delete_tag', 'web.view_tagscategory', 'web.add_tagscategory', 'web.change_tagscategory', 'web.delete_tagscategory']
    group = 'Админка'
    admin_only = True


class ManageForumPermission(BaseRolePermission):
    name = 'Управлять форумом'
    codename = 'manage_forum'
    description = 'Позволяет создавать, редактировать и удалять категории и разделы форума'
    represent_django_perms = ['web.view_forumcategory', 'web.add_forumcategory', 'web.change_forumcategory', 'web.delete_forumcategory', 'web.view_forumsection', 'web.add_forumsection', 'web.change_forumsection', 'web.delete_forumsection']
    group = 'Админка'
    admin_only = True


class ViewsensitiveInfoPermission(BaseRolePermission):
    name = 'Проссматривать чувствительную информацию'
    codename = 'view_sensitive_info'
    description = 'Позволяет просматривать чувствительную информацию пользователей, такую как почта или ip адрес'
    group = 'Админка'
    admin_only = True


class ViewVotesTimestampPermission(BaseRolePermission):
    name = 'Проссматривать время голоса'
    codename = 'view_votes_timestamp'
    description = 'Позволяет видеть дату и время простановки оценко статьи'
    group = 'Админка'
    admin_only = True
