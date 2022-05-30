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
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

import web.views.api.articles

from web.views.article import ArticleView


urlpatterns = [
    path('api/articles/new', csrf_exempt(web.views.api.articles.create)),
    path('api/articles/<str:full_name>', csrf_exempt(web.views.api.articles.fetch_or_update)),
    path('api/articles/<str:full_name>/log', csrf_exempt(web.views.api.articles.fetch_log)),
    re_path(r'(?P<path>.*)$', ArticleView.as_view())
]