from django.contrib.postgres.fields import CITextField
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    class UserType(models.TextChoices):
        Normal = 'normal'
        Wikidot = 'wikidot'
        System = 'system'

    username = CITextField(
        max_length=150,
        validators=[AbstractUser.username_validator],
        verbose_name="Имя пользователя",
        error_messages={
            "unique": "Пользователь с данным именем уже существует",
        }
    )

    type = models.TextField(choices=UserType.choices, default=UserType.Normal, verbose_name="Тип")

    avatar = models.ImageField(null=True, blank=True, upload_to='-/users', verbose_name="Аватар")
    bio = models.TextField(blank=True, verbose_name="Описание")

    def get_avatar(self, default=None):
        if self.avatar:
            return '%s%s' % (settings.MEDIA_URL, self.avatar)
        return default

    def __str__(self):
        return self.username
