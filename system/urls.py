from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

from django.urls import path, URLPattern, URLResolver
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import admin

from .views import PasswordResetView

from typing import Sequence, Union


_PathType = Union[URLPattern, URLResolver]


def make_path(url: str, *args, **kwargs) -> Sequence[_PathType]:
    return [
        path(f"{url}/", *args, **kwargs),
        path(url, RedirectView.as_view(url=f"/-/{url}/", permanent=True)),
    ]


urlpatterns = []
urlpatterns += make_path("admin", admin.site.urls)
urlpatterns += make_path("login", LoginView.as_view(template_name="login/login.html"), name="login")
urlpatterns += make_path("logout", LogoutView.as_view(next_page="/-/login/"), name="logout")
urlpatterns += make_path("password_reset", PasswordResetView.as_view(template_name="login/password_reset.html"), name="password_reset")
urlpatterns += make_path('password_reset/done', PasswordResetDoneView.as_view(template_name='login/password_reset_done.html'), name='password_reset_done')
urlpatterns += make_path('reset/<uidb64>/<token>', PasswordResetConfirmView.as_view(template_name="login/password_reset_confirm.html"), name='password_reset_confirm')
urlpatterns += make_path('reset/done', PasswordResetCompleteView.as_view(template_name='login/password_reset_complete.html'), name='password_reset_complete')
