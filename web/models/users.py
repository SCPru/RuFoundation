__all__ = [
    'User',
    'UsedToken'
]

import auto_prefetch
import re

from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, AnonymousUser
from django.db.models.functions import Lower
from django.db import models
from django.conf import settings

import web.fields
from web.models.roles import RolesMixin


class StrictUsernameValidator(RegexValidator):
    regex = r'^[\w.-]+\Z'
    message = 'Имя пользователя может содержать только английские буквы, цифры и символы [.-_] (без скобок).'
    flags = re.ASCII

class CSSValueValidator(RegexValidator):
    regex = r'^[^;\n\r]+\Z'
    message = 'CSS значение не может содержать ";" и переносы строк.'
    flags = re.ASCII


class ExtendedAnonymousUser(AnonymousUser):
    def get_avatar(self, default=None):
        return default or settings.DEFAULT_AVATAR

class User(AbstractUser, RolesMixin):
    class Meta(RolesMixin.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

        constraints = [
            models.UniqueConstraint(Lower('email'), name='user_email_ci_uniqueness',
            condition=models.Q(email__isnull=False) & ~models.Q(email=''))
        ]

        abstract = False

    class UserType(models.TextChoices):
        Normal = ('normal', 'Обычный')
        Wikidot = ('wikidot', 'Пользователь Wikidot')
        System = ('system', 'Системный')
        Bot = ('bot', 'Бот')

    username = web.fields.CITextField(
        max_length=150, validators=[StrictUsernameValidator()], unique=True,
        verbose_name='Имя пользователя',
        error_messages={
            'unique': 'Пользователь с данным именем уже существует',
        },
    )

    wikidot_username = web.fields.CITextField('Имя пользователя на Wikidot', unique=True, max_length=150, validators=[StrictUsernameValidator()], null=True, blank=False)

    type = models.TextField('Тип', choices=UserType.choices, default=UserType.Normal)

    avatar = models.ImageField('Аватар', null=True, blank=True, upload_to='-/users')
    bio = models.TextField('Описание', blank=True)

    api_key = models.CharField('Апи-ключ', unique=True, blank=True, null=True, max_length=67)

    is_forum_active = models.BooleanField('Активирован форум', default=True)
    forum_inactive_until = models.DateTimeField('Деактивировать форум до', null=True)

    is_active = models.BooleanField('Активирован', default=True)
    inactive_until = models.DateTimeField('Деактивировать до', null=True)

    is_staff = RolesMixin.is_staff # type: ignore

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
            return '/local--files/%s' % self.avatar
        return default

    def __str__(self):
        if self.type == User.UserType.Wikidot:
            return 'wd:%s' % (self.wikidot_username or self.username)
        return self.username

    def _generate_apikey(self, commit=True):
        self.password = ''
        self.api_key = make_password(self.username)[21:]
        if commit:
            self.save()

    def clean(self):
        super().clean()
        if self.username is None and self.wikidot_username is None:
            raise ValidationError('Имя пользователя или имя wikidot должно быть задано.')

    def save(self, *args, **kwargs):
        if not self.wikidot_username:
            self.wikidot_username = None
        if self.type == 'bot':
            if not self.api_key:
                self._generate_apikey(commit=False)
        else:
            self.api_key = None
        return super().save(*args, **kwargs)


class UsedToken(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = 'Использованный токен'
        verbose_name_plural = 'Использованные токены'

    token = models.TextField('Токен', null=False)
    is_case_sensitive = models.BooleanField('Чувствителен к регистру', null=False, default=True)

    @classmethod
    def is_used(cls, token):
        if cls.objects.filter(token=token, is_case_sensitive=True).exists():
            return True
        return cls.objects.filter(token__iexact=token, is_case_sensitive=False).exists()

    @classmethod
    def mark_used(cls, token, is_case_sensitive):
        cls(token=token, is_case_sensitive=is_case_sensitive).save()
