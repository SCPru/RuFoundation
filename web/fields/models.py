import re

from django.core import validators
from django.db import models

from . import widgets


__all__ = [
    'CIText',
    'CICharField',
    'CIEmailField',
    'CITextField',
    'CSSColorField'
]


class CSSHexColorValidator(validators.RegexValidator):
    regex = r"^#([0-9a-fA-F]{3}){1,2}$|^#([0-9a-fA-F]{4}){1,2}\Z"
    message = 'Неверный формат цвета, допускаются только hex значения (#000/#000000/#00000000).'
    flags = re.ASCII


class CIText:
    def get_internal_type(self):
        return "CI" + super().get_internal_type()

    def db_type(self, connection):
        return "citext"


class CICharField(CIText, models.CharField):
    pass


class CIEmailField(CIText, models.EmailField):
    pass


class CITextField(CIText, models.TextField):
    pass


class CSSColorField(models.CharField):
    default_validators = [CSSHexColorValidator()]

    def formfield(self, **kwargs):
        kwargs.update({'widget': widgets.ColorInput})
        return super().formfield(**kwargs)