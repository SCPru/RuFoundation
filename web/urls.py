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

from web.views.api.articles import CreateView, FetchOrUpdateView, FetchLogView
from web.views.article import ArticleView


urlpatterns = [
    path('api/articles/new', CreateView.as_view()),
    path('api/articles/<str:full_name>', FetchOrUpdateView.as_view()),
    path('api/articles/<str:full_name>/log', FetchLogView.as_view()),

    re_path(r'(?P<path>.*)$', ArticleView.as_view())
]