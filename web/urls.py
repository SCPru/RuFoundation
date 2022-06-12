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
from django.urls import path, re_path, include

from web.views.api.articles import CreateView, FetchOrUpdateView, FetchLogView
from web.views.api.preview import PreviewView
from web.views.api.module import ModuleView

from web.views.article import ArticleView


api_patterns = [
    path('articles/new', CreateView.as_view()),
    path('articles/<str:full_name>', FetchOrUpdateView.as_view()),
    path('articles/<str:full_name>/log', FetchLogView.as_view()),

    path('preview', PreviewView.as_view()),

    path('modules', ModuleView.as_view()),
]


urlpatterns = [
    path("api/", include(api_patterns)),

    re_path(r'(?P<path>.*)$', ArticleView.as_view())
]