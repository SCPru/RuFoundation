import auto_prefetch
import re

from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models

import web.fields
from web.models.roles import RolesMixin


__all__ = [
    'User',
    'UsedToken'
]


class StrictUsernameValidator(RegexValidator):
    regex = r"^[\w.-]+\Z"
    message = 'Имя пользователя может содержать только английские буквы, цифры и символы [.-_] (без скобок).'
    flags = re.ASCII

class CSSValueValidator(RegexValidator):
    regex = r"^[^;\n\r]+\Z"
    message = 'CSS значение не может содержать ";" и переносы строк.'
    flags = re.ASCII


class User(AbstractUser, RolesMixin):
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    class UserType(models.TextChoices):
        Normal = ('normal', 'Обычный')
        Wikidot = ('wikidot', 'Пользователь Wikidot')
        System = ('system', 'Системный')
        Bot = ('bot', 'Бот')

    username = web.fields.CITextField(
        max_length=150, validators=[StrictUsernameValidator()], unique=True,
        verbose_name="Имя пользователя",
        error_messages={
            "unique": "Пользователь с данным именем уже существует",
        },
    )

    wikidot_username = web.fields.CITextField(unique=True, max_length=150, validators=[StrictUsernameValidator()], verbose_name="Имя пользователя на Wikidot", null=True, blank=False)

    type = models.TextField(choices=UserType.choices, default=UserType.Normal, verbose_name="Тип")

    avatar = models.ImageField(null=True, blank=True, upload_to='-/users', verbose_name="Аватар")
    bio = models.TextField(blank=True, verbose_name="Описание")

    api_key = models.CharField(unique=True, blank=True, null=True, max_length=67, verbose_name="Апи-ключ")

    is_forum_active = models.BooleanField(verbose_name='Активирован форум', default=True)
    forum_inactive_until = models.DateTimeField(verbose_name='Деактивировать форум до', null=True)

    is_active = models.BooleanField(verbose_name='Активирован', default=True)
    inactive_until = models.DateTimeField(verbose_name='Деактивировать до', null=True)

    @property
    def is_staff(self):
        return self.is_superuser or RolesMixin.is_staff(self)
    
    @is_staff.setter
    def is_staff(self, new_value):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.inactive_until:
            self.is_active = False
        if self.inactive_until and not self.is_active and datetime.now(ZoneInfo('UTC')) > self.inactive_until:
            self.inactive_until = None
            self.is_active = True
        if self.forum_inactive_until:
            self.is_forum_active = False
        if self.forum_inactive_until and not self.is_forum_active and datetime.now(ZoneInfo('UTC')) > self.forum_inactive_until:
            self.forum_inactive_until = None
            self.is_forum_active = True

    def get_avatar(self, default=None):
        if self.avatar:
            return '%s%s' % ('/local--files/', self.avatar)
        return default

    def __str__(self):
        return self.username

    def _generate_apikey(self, commit=True):
        self.password = ""
        self.api_key = make_password(self.username)[21:]
        if commit:
            self.save()

    def save(self, *args, **kwargs):
        if not self.wikidot_username:
            self.wikidot_username = None
        if self.type == "bot":
            if not self.api_key:
                self._generate_apikey(commit=False)
        else:
            self.api_key = None
        return super().save(*args, **kwargs)


class UsedToken(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Использованный токен"
        verbose_name_plural = "Использованные токены"

    token = models.TextField(verbose_name='Токен', null=False)
    is_case_sensitive = models.BooleanField(verbose_name='Чувствителен к регистру', null=False, default=True)

    @classmethod
    def is_used(cls, token):
        used_sensitive = cls.objects.filter(token__exact=token)
        if used_sensitive:
            return True
        used_insensitive = cls.objects.filter(token__iexact=token)
        return used_insensitive and not used_insensitive[0].is_case_sensitive

    @classmethod
    def mark_used(cls, token, is_case_sensitive):
        cls(token=token, is_case_sensitive=is_case_sensitive).save()
