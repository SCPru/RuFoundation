from django.contrib.auth.models import AbstractUser
from django.shortcuts import resolve_url
from django.conf import settings
from django.db import models

from web.models.sites import get_current_site


class User(AbstractUser):
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    class UserType(models.TextChoices):
        Normal = 'normal'
        Wikidot = 'wikidot'
        System = 'system'

    type = models.TextField(choices=UserType.choices, default=UserType.Normal, verbose_name="Тип")

    avatar = models.ImageField(null=True, blank=True, upload_to='-/users', verbose_name="Аватар")
    bio = models.TextField(blank=True, verbose_name="Описание")

    def get_avatar(self):
        if self.avatar:
            return '%s%s' % (settings.MEDIA_URL, self.avatar)
        return settings.DEFAULT_AVATAR

    def __str__(self):
        return self.username
