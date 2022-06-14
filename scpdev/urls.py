"""scpdev URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.decorators.csrf import csrf_exempt
from django.urls import path, re_path, include
from django.conf import settings
import re
from pathlib import Path

import django.views.static

from web.models.sites import get_current_site


def partial_quote(url):
    return url.replace(':', '%3A')


def serve_static(request, dir_path, document_root=None, show_indexes=False):
    if not dir_path.startswith('-/'):
        site = get_current_site()
        document_root = Path(document_root) / site.slug
    dir_path = '/'.join([partial_quote(x) for x in dir_path.split('/')])
    return django.views.static.serve(request, dir_path, document_root=document_root, show_indexes=show_indexes)


urlpatterns = [
    re_path(r'^%s(?P<dir_path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')), serve_static, {'document_root': settings.MEDIA_ROOT}, name="local_files"),

    path("-/", include("system.urls")),
    path("", include("web.urls"))
]
