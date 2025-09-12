__all__ = [
    'PermissionsField',
    'PermissionsOverrideField'
]

from django import forms

from web.models.roles import Role
from . import widgets


class PermissionsField(forms.Field):
    widget = widgets.PermissionsInput

    def clean(self, value):
        if not isinstance(value, dict):
            raise forms.ValidationError("Invalid permissions data")

        cleaned = {
            'allow': [],
            'deny': [],
            'neutral': []
        }

        for codename, state in value.items():
            if state not in cleaned:
                raise forms.ValidationError(f"Invalid state: {state}")
            cleaned[state].append(codename)

        return cleaned
    

class PermissionsOverrideField(forms.Field):
    widget = widgets.PermissionsOverrideInput

    def __init__(self, *args, exclude_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.exclude_admin = exclude_admin

    def clean(self, value):
        if not isinstance(value, dict):
            raise forms.ValidationError("Invalid permissions data")

        cleaned = {}

        for role_id, perms in value.items():
            try:
                Role.objects.get(id=role_id)
            except:
                forms.ValidationError(f"Invalid role id: {role_id}")

            cleaned[role_id] = {
                'allow': [],
                'deny': [],
                'neutral': []
            }

            for codename, state in perms.items():
                if state not in cleaned[role_id]:
                    raise forms.ValidationError(f"Invalid state: {state}")
                cleaned[role_id][state].append(codename)

        return cleaned
