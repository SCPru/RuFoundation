from django.contrib.auth.backends import BaseBackend

from web.models.roles import Role, PermissionsOverrideMixin
from web.permissions import _ROLE_PERMISSIONS_REPR_CACHE


class RolesBackend(BaseBackend):
    
    def get_all_permissions(self, user_obj, obj: PermissionsOverrideMixin=None):
        if not user_obj.is_active and not user_obj.is_anonymous:
            return set()

        roles_cache = getattr(user_obj, '_roles_cache', None)
        if roles_cache is None:
            roles_cache = [Role.get_or_create_default_role()]
            if not user_obj.is_anonymous:
                roles_cache.append(Role.get_or_create_registered_role())
                roles_cache.extend(user_obj.roles.all().order_by('-index'))
            user_obj._roles_cache = roles_cache

        perms = set()
        has_override = isinstance(obj, PermissionsOverrideMixin)

        for role in roles_cache:
            role_perms = {f'roles.{p.codename}' for p in role.permissions.all()}
            role_restricts = {f'roles.{p.codename}' for p in role.restrictions.all()}
            role_final = role_perms - role_restricts

            if has_override:
                role_final = obj.override_role(user_obj, role_final, role)

            perms.update(role_final)

        if has_override:
            perms = obj.override_perms(user_obj, perms, roles_cache)

        return perms
    
    def has_perm(self, user_obj, perm, obj: PermissionsOverrideMixin=None):
        is_cachable = obj is None or (obj.pk if hasattr(obj, 'pk') else (hasattr(obj, '__hash__') and obj.__hash__ is not None))
        if is_cachable and hasattr(user_obj, '_roles_perms_cache') and (obj, perm) in user_obj._roles_perms_cache:
            return user_obj._roles_perms_cache[(obj, perm)]
        else:
            user_obj._roles_perms_cache = {}
        all_perms = self.get_all_permissions(user_obj, obj)
        if perm in _ROLE_PERMISSIONS_REPR_CACHE:
            for role_perm in _ROLE_PERMISSIONS_REPR_CACHE[perm]:
                if role_perm in all_perms:
                    if is_cachable:
                        user_obj._roles_perms_cache[(obj, perm)] = True
                    return True
        result = perm in all_perms
        if is_cachable:
            user_obj._roles_perms_cache[(obj, perm)] = result
        return result
    
    def has_module_perms(self, user_obj, app_label):
        return True
