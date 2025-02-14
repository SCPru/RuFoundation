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
import os.path

import django.views.static

from web.controllers import articles
from web.models.site import get_current_site


def partial_quote(url):
    return url.replace(':', '%3A').replace('/', '%2F').replace('?', '%3F')


def serve_static(request, dir_path, document_root=None, show_indexes=False):
    if not dir_path.startswith('-/'):
        site = get_current_site()
        document_root = Path(document_root) / site.slug

    # we need to check if dir path does not exist. if it doesn't, look for possible file remap (name->media_name)
    # to be changed later somehow.
    # the current setup allows serving both UUID-remapped files and avatars/etc from the same path
    dir_path_split = dir_path.split('/')
    if len(dir_path_split) == 2:
        exists = os.path.exists(document_root / Path(dir_path))
        if not exists:
            article = articles.get_article(dir_path_split[0])
            if article:
                file = articles.get_file_in_article(article, dir_path_split[1])
                if file:
                    dir_path_split[1] = file.media_name
                    dir_path_split[0] = article.media_name
    dir_path = '/'.join([partial_quote(x) for x in dir_path_split])

    response = django.views.static.serve(request, dir_path, document_root=document_root, show_indexes=show_indexes)
    response['Content-Disposition'] = "inline"
    return response


urlpatterns = [
    re_path(r'^%s(?P<dir_path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')), serve_static, {'document_root': settings.MEDIA_ROOT}, name="local_files_generic"),

    path("", include("web.urls"))
]
