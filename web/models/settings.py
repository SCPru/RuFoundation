from django.db import models


class Settings(models.Model):
    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"

    class RatingMode(models.TextChoices):
        Disabled = 'disabled'
        UpDown = 'updown'
        Stars = 'stars'

    type = models.TextField(choices=RatingMode.choices, default=None, verbose_name="Система рейтинга", null=True)

    # overwrites whatever fields that are not null with values from the other object.
    # returns a copy.
    def merge(self, other: 'Settings') -> 'Settings':
        new_settings = Settings()
        new_settings.type = other.type if other.type is not None else self.type
        return new_settings


# Hierarchy:
# DEFAULT_SETTINGS -> site settings -> category settings
DEFAULT_SETTINGS = Settings(type=Settings.RatingMode.UpDown)
