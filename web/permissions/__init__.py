import sys
import pkgutil
import logging

from importlib.util import module_from_spec

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.dispatch import receiver

import web.signals
import web.models

from web.util import check_function_exists_and_callable


_ROLE_PERMISSIONS_REPR_CACHE = {}
ROLE_PERMISSIONS_CONTENT_TYPE = None


def get_role_permissions_content_type():
    global ROLE_PERMISSIONS_CONTENT_TYPE
    if not ROLE_PERMISSIONS_CONTENT_TYPE:
        ROLE_PERMISSIONS_CONTENT_TYPE, _ = ContentType.objects.get_or_create(
            app_label='web',
            model='roles'
        )
    return ROLE_PERMISSIONS_CONTENT_TYPE


class BaseRolePermission:
    name = None
    codename = None
    description = None
    admin_only = False
    group = None
    represent_django_perms = []

    @classmethod
    def as_permission(cls):
        return Permission.objects.get(
            codename=cls.codename,
            content_type=get_role_permissions_content_type(),
        )
    
    def __str__(self):
        return f'roles.{self.__class__.codename}'


ALL_PERMISSIONS: dict[str, BaseRolePermission] = {}


class RolePermissionRegistrationError(Exception):
    pass


def _preload_role_permissions():
    package = sys.modules[__name__]
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        try:
            spec = importer.find_spec(modname)
            m = module_from_spec(spec)
            spec.loader.exec_module(m)
            if not check_function_exists_and_callable(m, 'is_perms_collection'):
                continue
            if not m.is_perms_collection():
                continue
            logging.info('Loaded permissions collection \'%s\'', modname.lower())
        except:
            logging.error('Failed to load permissions collection \'%s\':', modname.lower(), exc_info=True)
            continue


def register_role_permissions():
    global _ROLE_PERMISSIONS_REPR_CACHE, ALL_PERMISSIONS

    import web.permissions.admin
    import web.permissions.forum
    import web.permissions.articles
    # Temporary disabled because paws
    # _preload_role_permissions()

    content_type = get_role_permissions_content_type()
    permissions = BaseRolePermission.__subclasses__()

    actual_perms = []

    for perm in permissions:
        if not perm.name or not perm.codename:
            raise RolePermissionRegistrationError('Role permissions must have name and codename.')

        new_perm, _ = Permission.objects.get_or_create(
            codename=perm.codename,
            content_type=content_type,
        )
        new_perm.name = perm.name

        ALL_PERMISSIONS[perm.codename] = (perm)

        actual_perms.append(new_perm.codename)

        for perm_repr in perm.represent_django_perms:
            codename = f'roles.{perm.codename}'
            if perm_repr in _ROLE_PERMISSIONS_REPR_CACHE:
                _ROLE_PERMISSIONS_REPR_CACHE[perm_repr].append(codename)
            else:
                _ROLE_PERMISSIONS_REPR_CACHE[perm_repr] = [codename]

    Permission.objects.filter(content_type=content_type).exclude(codename__in=actual_perms).delete()


@receiver(web.signals.just_after_migration)
def handle_migration(sender, action, migration, **kwargs):
    if action == 'apply_success':
        if migration == 'web.0056':
            register_role_permissions()
        if migration == 'web.0057':
            assign_default_permissions()


def assign_default_permissions():
    readers_perms = ['rate_articles', 'comment_articles', 'create_forum_threads', 'create_forum_posts']
    editors_perms = ['create_articles', 'edit_articles', 'tag_articles', 'move_articles', 'manage_article_files', 'reset_article_votes']
    everyone_perms = ['view_articles', 'view_article_comments', 'view_forum_sections', 'view_forum_categories', 'view_forum_threads', 'view_forum_posts']

    content_type = get_role_permissions_content_type()

    web.models.Role.objects.get(slug='everyone').permissions.set(Permission.objects.filter(codename__in=everyone_perms, content_type=content_type))
    web.models.Role.objects.get(slug='reader').permissions.set(Permission.objects.filter(codename__in=readers_perms, content_type=content_type))
    web.models.Role.objects.get(slug='editor').permissions.set(Permission.objects.filter(codename__in=editors_perms, content_type=content_type))