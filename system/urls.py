from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

from django.urls import path, URLPattern, URLResolver
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import admin

from .views import login, profile

from typing import List, Union


_PathType = Union[URLPattern, URLResolver]


def make_path(url: str, *args, **kwargs) -> List[_PathType]:
    return [
        path(f"{url}/", *args, **kwargs),
        path(url, RedirectView.as_view(url=f"/-/{url}/", permanent=True)),
    ]


urlpatterns = [
    path("login", LoginView.as_view(template_name="login/login.html"), name="login"),
    path("logout", LogoutView.as_view(next_page="/-/login/"), name="logout"),
    path("password_reset", login.PasswordResetView.as_view(template_name="login/password_reset.html"), name="password_reset"),
    path('password_reset/done', PasswordResetDoneView.as_view(template_name='login/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>', PasswordResetConfirmView.as_view(template_name="login/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done', PasswordResetCompleteView.as_view(template_name='login/password_reset_complete.html'), name='password_reset_complete'),
    path("users/<slug:slug>", profile.ProfileView.as_view(template_name="profile/user.html"))
] + make_path("admin", admin.site.urls)
