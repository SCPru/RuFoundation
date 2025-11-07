from django.contrib.auth.backends import BaseBackend

from web.models.roles import Role, PermissionsOverrideMixin
from web.permissions import _ROLE_PERMISSIONS_REPR_CACHE

class RolesBackend(BaseBackend):
    def get_all_permissions(self, user_obj, obj: PermissionsOverrideMixin=None):
        if not user_obj.is_active and not user_obj.is_anonymous:
            return set()
        if not hasattr(user_obj, '_roles_cache'):
            user_obj._roles_cache = [Role.get_or_create_default_role()]
            if not user_obj.is_anonymous:
                user_obj._roles_cache += [Role.get_or_create_registered_role()]
                user_obj._roles_cache += [role for role in user_obj.roles.all().order_by('-index')]

        perms = set()
        has_override = issubclass(obj.__class__, PermissionsOverrideMixin)

        for role in user_obj._roles_cache:
            for perm in role.permissions.all():
                codename = f'roles.{perm.codename}'
                perms.add(codename)

            for perm in role.restrictions.all():
                codename = f'roles.{perm.codename}'
                if codename in perms:
                    perms.remove(codename)

            if has_override:
                perms = obj.override_role(user_obj, perms, role)

        if has_override:
            perms = obj.override_perms(user_obj, perms, user_obj._roles_cache)

        return perms
    
    def has_perm(self, user_obj, perm, obj: PermissionsOverrideMixin=None):
        all_perms = self.get_all_permissions(user_obj, obj)
        if perm in _ROLE_PERMISSIONS_REPR_CACHE:
            for role_perm in _ROLE_PERMISSIONS_REPR_CACHE[perm]:
                if role_perm in all_perms:
                    return True
        return perm in all_perms
    
    def has_module_perms(self, user_obj, app_label):
        return True
