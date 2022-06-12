from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models


class Profile(models.Model):
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Пользователь")

    avatar = models.ImageField(default='../static/images/default_avatar.png', blank=True, upload_to='-/users', verbose_name="Аватар")
    bio = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_favorites(instance: User, created: bool, **kwargs):
    if created:
        Profile.objects.create(user=instance)
