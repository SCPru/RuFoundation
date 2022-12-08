import auto_prefetch
from django.db import models


class Settings(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"

    class RatingMode(models.TextChoices):
        Default = 'default'
        Disabled = 'disabled'
        UpDown = 'updown'
        Stars = 'stars'

    class UserCreateTagsMode(models.TextChoices):
        Default = 'default'
        Disabled = 'disabled'
        Enabled = 'enabled'

    site = auto_prefetch.OneToOneField('Site', on_delete=models.CASCADE, null=True, related_name='_settings')
    category = auto_prefetch.OneToOneField('Category', on_delete=models.CASCADE, null=True, related_name='_settings')

    rating_mode = models.TextField(choices=RatingMode.choices, default=RatingMode.Default, verbose_name="Система рейтинга", null=False)
    can_user_create_tags = models.TextField(choices=UserCreateTagsMode.choices, default=UserCreateTagsMode.Default, verbose_name="Может ли пользователь создавать теги", null=False)

    # Hierarchy:
    # DEFAULT_SETTINGS -> site settings -> category settings
    @classmethod
    def get_default_settings(cls):
        return cls(rating_mode=Settings.RatingMode.UpDown, can_user_create_tags=Settings.UserCreateTagsMode.Enabled)

    # overwrites whatever fields that are not null with values from the other object.
    # returns a copy.
    def merge(self, other: 'Settings') -> 'Settings':
        new_settings = Settings()
        new_settings.rating_mode = other.rating_mode if other.rating_mode != Settings.RatingMode.Default else self.rating_mode
        new_settings.can_user_create_tags = other.can_user_create_tags if other.can_user_create_tags != Settings.UserCreateTagsMode.Default else self.can_user_create_tags
        return new_settings

    @property
    def creating_tags_allowed(self) -> bool:
        return self.can_user_create_tags == Settings.UserCreateTagsMode.Enabled


