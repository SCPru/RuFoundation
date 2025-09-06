import sys
import pkgutil
import logging
from importlib.util import module_from_spec

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission


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
            if not getattr(m, 'is_perms_collection', False):
                continue
            logging.info('Loaded permissions collection \'%s\'', modname.lower())
        except:
            logging.error('Failed to load permissions collection \'%s\':', modname.lower(), exc_info=True)
            continue


def register_role_permissions():
    global _ROLE_PERMISSIONS_REPR_CACHE, ALL_PERMISSIONS
    _preload_role_permissions()

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