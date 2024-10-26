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

from web.views.api import articles, preview, module, files

from web.views.article import ArticleView


api_patterns = [
    path('articles', articles.AllArticlesView.as_view()),
    path('articles/new', articles.CreateView.as_view()),
    path('articles/<str:full_name>/version', articles.FetchVersionView.as_view()),
    path('articles/<str:full_name>', articles.FetchOrUpdateView.as_view()),
    path('articles/<str:full_name>/log', articles.FetchOrRevertLogView.as_view()),
    path('articles/<str:full_name>/links', articles.FetchExternalLinks.as_view()),
    path('articles/<str:full_name>/votes', articles.FetchOrUpdateVotesView.as_view()),

    path('articles/<str:article_name>/files', files.GetOrUploadView.as_view()),
    path('files/<int:file_id>', files.RenameOrDeleteView.as_view()),

    path('preview', preview.PreviewView.as_view()),

    path('modules', module.ModuleView.as_view()),
]


urlpatterns = [
    path("api/", include(api_patterns)),

    re_path(r'(?P<path>.*)$', ArticleView.as_view())
]