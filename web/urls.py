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

from typing import List, Union

from django.views.generic.base import RedirectView
from django.views.decorators.csrf import csrf_exempt
from django.urls import path, re_path, include, URLPattern, URLResolver
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetView
from django.contrib import admin

from .views import profile, signup, login

from web.views.api import articles, preview, module, files, notifications, users, search
from web.views.article import ArticleView
from web.views.reactive import reactive_view


_PathType = Union[URLPattern, URLResolver]


def make_path(url: str, *args, **kwargs) -> List[_PathType]:
    return [
        path(f"{url}/", *args, **kwargs),
        path(url, RedirectView.as_view(url=f"/-/{url}/", permanent=True)),
    ]


def make_reactive(routes: list[str]):
    return [path(route, reactive_view) for route in routes]


api_patterns = [
    path('users', users.AllUsersView.as_view()),
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

    path('modules', csrf_exempt(module.ModuleView.as_view())),

    path('notifications', notifications.NotificationsView.as_view()),
    path('notifications/subscribe', notifications.NotificationsSubscribeView.as_view()),

    path('search', search.SearchView.as_view())
]


reactive_pages = [
    'notifications',
    'profile',
    'notifications/all',
    'notifications/unread',
    'search'
]


sys_patterns = [
    path("login", login.LoginView.as_view(), name='login'),
    path("logout", login.LogoutView.as_view()),
    path("password_reset", PasswordResetView.as_view(
            template_name="login/password_reset.html",
            email_template_name="mails/password_reset_email.txt"),
        name="password_reset"),
    path('password_reset/done', PasswordResetDoneView.as_view(template_name='login/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>', PasswordResetConfirmView.as_view(template_name="login/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done', PasswordResetCompleteView.as_view(template_name='login/password_reset_complete.html'), name='password_reset_complete'),

    path("users/<int:pk>-<slug>", profile.ProfileView.as_view(template_name="profile/user.html"), name="users"),
    path("profile/edit", profile.ChangeProfileView.as_view(template_name="profile/change.html"), name="profile_edit"),

    path('accept/<uidb64>/<token>', signup.AcceptInvitationView.as_view(), name="accept"),

    *make_path("admin", admin.site.urls),
    *make_reactive(reactive_pages)
]


urlpatterns = [
    path("-/", include(sys_patterns)),
    path("api/", include(api_patterns)),

    re_path(r'(?P<path>.*)$', ArticleView.as_view())
]