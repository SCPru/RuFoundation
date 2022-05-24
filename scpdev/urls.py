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
from django.contrib import admin
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

import django.views.static
import urllib.parse

import web.views.article

import web.views.api.articles


def partial_quote(url):
    return url.replace(':', '%3A')


def serve_static(request, path, document_root=None, show_indexes=False):
    path = '/'.join([partial_quote(x) for x in path.split('/')])
    return django.views.static.serve(request, path, document_root=document_root, show_indexes=show_indexes)


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/articles/new', csrf_exempt(web.views.api.articles.create)),
    path('api/articles/<str:full_name>', csrf_exempt(web.views.api.articles.fetch_or_update)),
    path('api/articles/<str:full_name>/log', csrf_exempt(web.views.api.articles.fetch_log)),

    re_path(r'^static/(?P<path>.*$)', serve_static, {'document_root': './web/static'}),
    re_path(r'^local--files/(?P<path>.*)$', serve_static, {'document_root': './files'}),
    re_path(r'(?P<path>.*)$', web.views.article.index)
]
