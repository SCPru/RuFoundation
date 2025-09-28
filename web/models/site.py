__all__ = [
    'Site',
    'get_current_site'
]

from functools import cached_property
from typing import Optional

from solo.models import SingletonModel
from django.db import models

from web import threadvars
from .settings import Settings


class Site(SingletonModel):
    class Meta(SingletonModel.Meta):
        verbose_name = 'Сайт'
        verbose_name_plural = 'Сайты'

        constraints = [
            models.UniqueConstraint(fields=['domain'], name='%(app_label)s_%(class)s_domain_unique'),
            models.UniqueConstraint(fields=['slug'], name='%(app_label)s_%(class)s_slug_unique'),
        ]

    slug = models.TextField('Сокращение', null=False)

    title = models.TextField('Заголовок', null=False)
    headline = models.TextField('Подзаголовок', null=False)
    icon = models.ImageField('Иконка', null=True, blank=True, upload_to='-/sites')

    domain = models.TextField('Домен для статей', null=False)
    media_domain = models.TextField('Домен для файлов', null=False)

    @cached_property
    def settings(self):
        return Settings.objects.filter(site=self).first() or Settings.get_default_settings()

    def __str__(self) -> str:
        return f'{self.title} ({self.domain})'


def get_current_site(required=True) -> Optional[Site]:
    site = threadvars.get('current_site')
    if site is None and required:
        raise ValueError('There is no current site while it was required')
    return site
