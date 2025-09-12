__all__ = [
    'ColorInput',
    'PermissionsInput'
]

from django import forms

from web.permissions import ALL_PERMISSIONS


class ColorInput(forms.TextInput):
    input_type = 'color'


class PermissionsInput(forms.Widget):
    template_name = 'fields/permissions_widget.html'

    def value_from_datadict(self, data, files, name):
        result = {}
        for key in data:
            if key.startswith('perm-'):
                codename = key[5:]
                value = data.get(key)
                result[codename] = value
        return result

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['perms'] = {}

        if self.instance:
            permissions = [perm.codename for perm in self.instance.permissions.all()]
            restrictions = [perm.codename for perm in self.instance.restrictions.all()]
        else:
            permissions = []
            restrictions = []

        for perm in ALL_PERMISSIONS.values():
            state = 'neutral'
            if perm.codename in permissions:
                state = 'allow'
            elif perm.codename in restrictions:
                state = 'deny'

            if not perm.group in context['perms']:
                context['perms'][perm.group] = []
            
            context['perms'][perm.group].append({
                'name': perm.name,
                'codename': perm.codename,
                'description': perm.description,
                'allow': state == 'allow',
                'deny': state == 'deny',
                'neutral': state == 'neutral',
            })

        for perm_group in context['perms']:
            context['perms'][perm_group].sort(
                key=lambda perm: perm['codename']
                                    .replace('view', '0')
                                    .replace('create', '1')
                                    .replace('edit', '2')
                                    .replace('delete', '3')
            )
        
        return context
    

class PermissionsOverrideInput(forms.Widget):
    template_name = 'fields/permissions_override_widget.html'

    def __init__(self, *args, exclude_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.exclude_admin = exclude_admin


    def value_from_datadict(self, data, files, name):
        result = {}
        for key in data:
            if key.startswith('perm-'):
                _, role_id, codename = key.split('-', 2)
                value = data.get(key)
                if role_id not in result:
                    result[role_id] = {}
                result[role_id][codename] = value
        return result

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['roles'] = []

        if self.instance:
            perm_overrides = self.instance.permissions_override.all().order_by('role__index')
        else:
            perm_overrides = []

        for perm_override in perm_overrides:
            permissions = [perm.codename for perm in perm_override.permissions.all()]
            restrictions = [perm.codename for perm in perm_override.restrictions.all()]

            context['roles'].append({
                'role': perm_override.role,
                'perms': {}
            })

            for perm in ALL_PERMISSIONS.values():
                if self.exclude_admin and perm.admin_only:
                    continue
                
                state = 'neutral'
                if perm.codename in permissions:
                    state = 'allow'
                elif perm.codename in restrictions:
                    state = 'deny'

                if not perm.group in context['roles'][-1]['perms']:
                    context['roles'][-1]['perms'][perm.group] = []
                
                context['roles'][-1]['perms'][perm.group].append({
                    'name': perm.name,
                    'codename': perm.codename,
                    'description': perm.description,
                    'allow': state == 'allow',
                    'deny': state == 'deny',
                    'neutral': state == 'neutral',
                })

            for n, role in enumerate(context['roles']):
                for perm_group in role['perms']:
                    context['roles'][n]['perms'][perm_group].sort(
                        key=lambda perm: perm['codename']
                                            .replace('view', '0')
                                            .replace('create', '1')
                                            .replace('edit', '2')
                                            .replace('delete', '3')
                    )
        
        return context
