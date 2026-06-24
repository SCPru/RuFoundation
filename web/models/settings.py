__all__ = [
    'Settings'
]

import auto_prefetch

from typing import Optional

from django.core.validators import MinValueValidator
from django.db import models


class Settings(auto_prefetch.Model):
    class Meta(auto_prefetch.Model.Meta):
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"

    class RatingMode(models.TextChoices):
        Default = ('default', 'По умолчанию')
        Disabled = ('disabled', 'Отключено')
        UpDown = ('updown', 'Апвоуты')
        Stars = ('stars', 'Звёзды')

    class UserCreateTagsMode(models.TextChoices):
        Default = ('default', 'По умолчанию')
        Disabled = ('disabled', 'Запрещено')
        Enabled = ('enabled', 'Разрешено')

    site = auto_prefetch.OneToOneField('Site', on_delete=models.CASCADE, null=True, related_name='_settings')
    category = auto_prefetch.OneToOneField('Category', on_delete=models.CASCADE, null=True, related_name='_settings')

    rating_mode = models.TextField(choices=RatingMode.choices, default=RatingMode.Default, verbose_name="Система рейтинга", null=False)
    can_user_create_tags = models.TextField(choices=UserCreateTagsMode.choices, default=UserCreateTagsMode.Default, verbose_name="Может ли пользователь создавать теги", null=False)
    forum_reactions_per_user = models.PositiveIntegerField(
        "Максимум реакций пользователя под сообщением",
        default=20,
        help_text="Сколько разных реакций один пользователь может поставить под одним сообщением. 0 отключает новые реакции.",
    )
    forum_reaction_types_per_post = models.PositiveIntegerField(
        "Максимум типов реакций под сообщением",
        default=20,
        help_text="Сколько разных типов реакций можно показать под одним сообщением. Пользователи могут добавлять уже показанные типы сверх этого лимита. 0 отключает новые реакции.",
    )
    forum_post_max_depth = models.PositiveIntegerField(
        "Максимальная вложенность постов",
        default=5,
        validators=[MinValueValidator(1)],
        help_text="Глубина отображения дерева ответов. Ответы глубже этого значения показываются на максимальном уровне вложенности.",
    )

    # Hierarchy:
    # DEFAULT_SETTINGS -> site settings -> category settings
    @classmethod
    def get_default_settings(cls):
        return cls(
            rating_mode=Settings.RatingMode.Stars,
            can_user_create_tags=Settings.UserCreateTagsMode.Disabled,
            forum_reactions_per_user=20,
            forum_reaction_types_per_post=20,
            forum_post_max_depth=5,
        )

    # overwrites whatever fields that are not null with values from the other object.
    # returns a copy.
    def merge(self, other: Optional['Settings']) -> 'Settings':
        if other is None:
            return self
        new_settings = Settings()
        new_settings.rating_mode = other.rating_mode if other.rating_mode != Settings.RatingMode.Default else self.rating_mode
        new_settings.can_user_create_tags = other.can_user_create_tags if other.can_user_create_tags != Settings.UserCreateTagsMode.Default else self.can_user_create_tags
        new_settings.forum_reactions_per_user = other.forum_reactions_per_user
        new_settings.forum_reaction_types_per_post = other.forum_reaction_types_per_post
        new_settings.forum_post_max_depth = other.forum_post_max_depth
        return new_settings

    @property
    def creating_tags_allowed(self) -> bool:
        return self.can_user_create_tags == Settings.UserCreateTagsMode.Enabled
