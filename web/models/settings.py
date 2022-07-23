from django.db import models


class Settings(models.Model):
    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"

    class RatingMode(models.TextChoices):
        Default = None
        Disabled = 'disabled'
        UpDown = 'updown'
        Stars = 'stars'

    site = models.OneToOneField('Site', on_delete=models.CASCADE, null=True, related_name='settings')
    category = models.OneToOneField('Category', on_delete=models.CASCADE, null=True, related_name='settings')

    rating_mode = models.TextField(choices=RatingMode.choices, default=None, verbose_name="Система рейтинга", null=True)

    # Hierarchy:
    # DEFAULT_SETTINGS -> site settings -> category settings
    @classmethod
    def get_default_settings(cls):
        return cls(rating_mode=Settings.RatingMode.UpDown)

    # overwrites whatever fields that are not null with values from the other object.
    # returns a copy.
    def merge(self, other: 'Settings') -> 'Settings':
        new_settings = Settings()
        new_settings.type = other.rating_mode if other.rating_mode is not None else self.rating_mode
        return new_settings


