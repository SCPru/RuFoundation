from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

from django.urls import path, URLPattern, URLResolver
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetView
from django.contrib import admin

from .views import profile, signup

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
    path("password_reset", PasswordResetView.as_view(template_name="login/password_reset.html",
                                                     email_template_name="mails/password_reset_email.html"),
         name="password_reset"),
    path('password_reset/done', PasswordResetDoneView.as_view(template_name='login/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>', PasswordResetConfirmView.as_view(template_name="login/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done', PasswordResetCompleteView.as_view(template_name='login/password_reset_complete.html'), name='password_reset_complete'),

    path("users/<slug:slug>", profile.ProfileView.as_view(template_name="profile/user.html"), name="users"),
    path("profile", profile.MyProfileView.as_view(template_name="profile/user.html"), name="profile"),
    path("profile/edit", profile.ChangeProfileView.as_view(template_name="profile/change.html"), name="profile_edit"),

    path('accept/<uidb64>/<token>', signup.ActivateView.as_view(template_name="signup/accept.html"), name='accept'),
] + make_path("admin", admin.site.urls)
