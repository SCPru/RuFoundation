from typing import Union, Sequence, Optional

from django.db import models
from web import threadvars

from .settings import Settings


class Site(models.Model):
    class Meta:
        verbose_name = "Сайт"
        verbose_name_plural = "Сайты"

        constraints = [
            models.UniqueConstraint(fields=['domain'], name='%(app_label)s_%(class)s_domain_unique'),
            models.UniqueConstraint(fields=['slug'], name='%(app_label)s_%(class)s_slug_unique'),
        ]

    slug = models.TextField(verbose_name='Сокращение', null=False)

    title = models.TextField(verbose_name='Заголовок', null=False)
    headline = models.TextField(verbose_name='Подзаголовок', null=False)
    icon = models.ImageField(null=True, blank=True, upload_to='-/sites', verbose_name="Иконка")

    domain = models.TextField(verbose_name='Домен для статей', null=False)
    media_domain = models.TextField(verbose_name='Домен для файлов', null=False)

    def get_settings(self):
        return Settings.objects.filter(site=self).first() or Settings.get_default_settings()

    def __str__(self) -> str:
        return f"{self.title} ({self.domain})"


# This should be used with metaclass=, not parent class name.
# Example: class Tag(metaclass=_SiteLimitedMetaclass)
class _SiteLimitedMetaclass(models.base.ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        # Same as in ModelBase.
        parents = [b for b in bases if isinstance(b, _SiteLimitedMetaclass)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # add site field
        if 'site' in attrs:
            raise KeyError('Field \'site\' already exists in \'%s\'. This is not compatible with SiteLimitedModel.' % name)
        attrs['site'] = models.ForeignKey(to=Site, on_delete=models.CASCADE, null=False, verbose_name="Сайт")

        # modify unique constraints and add site field
        meta = attrs.get('Meta')
        if meta:
            constraints = getattr(meta, 'constraints', None)
            if constraints:
                for i in range(len(constraints)):
                    constraint = constraints[i]
                    if isinstance(constraint, models.UniqueConstraint):
                        if 'site' not in constraint.fields:
                            constraint.fields = ('site',) + constraint.fields

        # call regular model creator
        new_class = super_new(cls, name, bases, attrs)

        # add site reference
        return new_class

    def __getattribute__(cls, attr):
        parent = super().__getattribute__(attr)
        if attr != 'objects':
            return parent
        site_filter = get_cross_site_filter()
        if site_filter == 'all':
            return parent
        return parent.filter(site__in=site_filter)


class SiteLimitedModel(models.Model, metaclass=_SiteLimitedMetaclass):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._state.adding:
            self.site = get_current_site()


def get_current_site(required=True) -> Optional[Site]:
    site = threadvars.get('current_site')
    if site is None and required:
        raise ValueError('There is no current site while it was required')
    return site


def get_cross_site_filter() -> Union['all', Sequence[Site]]:
    f = threadvars.get('cross_site_filter')
    site = get_current_site(required=False)
    if f is None and site:
        return [site]
    if f is None and not site:
        return 'all'
    return f


class CrossSiteFilterContext(object):
    def __init__(self, f):
        self.filter = f
        self.context = threadvars.context()

    def __enter__(self):
        self.context.__enter__()
        threadvars.put('cross_site_filter', self.filter)

    def __exit__(self, *args, **kwargs):
        return self.context.__exit__(*args, **kwargs)


def cross_site_filter(f: Sequence[Union[str, Site]]):
    new_filter = []
    for i in range(len(f)):
        if type(f[i]) == 'str':
            try:
                site = Site.objects.get(slug=f[i])
            except:
                site = None
            if not site:
                raise ValueError('Unknown cross-site slug \'%s\'' % f[i])
            new_filter.append(site)
        else:
            new_filter.append(f[i])
    return CrossSiteFilterContext(new_filter)
