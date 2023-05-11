from django.contrib.postgres.fields import CITextField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from datetime import datetime
from zoneinfo import ZoneInfo


class User(AbstractUser):
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    class UserType(models.TextChoices):
        Normal = 'normal'
        Wikidot = 'wikidot'
        System = 'system'
        Bot = 'bot'

    username = CITextField(
        max_length=150, validators=[AbstractUser.username_validator], unique=True,
        verbose_name="Имя пользователя",
        error_messages={
            "unique": "Пользователь с данным именем уже существует",
        },
    )

    wikidot_username = CITextField(unique=True, max_length=150, validators=[AbstractUser.username_validator], verbose_name="Имя пользователя на Wikidot", null=True, blank=False)

    type = models.TextField(choices=UserType.choices, default=UserType.Normal, verbose_name="Тип")

    avatar = models.ImageField(null=True, blank=True, upload_to='-/users', verbose_name="Аватар")
    bio = models.TextField(blank=True, verbose_name="Описание")

    api_key = models.CharField(unique=True, blank=True, null=True, max_length=67, verbose_name="Апи-ключ")

    is_forum_active = models.BooleanField(verbose_name='Активирован форум', default=True)
    forum_inactive_until = models.DateTimeField(verbose_name='Деактивировать форум до', null=True)

    is_active = models.BooleanField(verbose_name='Активирован', default=True)
    inactive_until = models.DateTimeField(verbose_name='Деактивировать до', null=True)

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
            return '%s%s' % (settings.MEDIA_URL, self.avatar)
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
