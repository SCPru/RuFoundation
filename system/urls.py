from django.views.generic.base import RedirectView

from django.urls import path, URLPattern, URLResolver
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetView
from django.contrib import admin

from .views import profile, signup, login

from typing import List, Union


_PathType = Union[URLPattern, URLResolver]


def make_path(url: str, *args, **kwargs) -> List[_PathType]:
    return [
        path(f"{url}/", *args, **kwargs),
        path(url, RedirectView.as_view(url=f"/-/{url}/", permanent=True)),
    ]


urlpatterns = [
    path("login", login.LoginView.as_view(), name='login'),
    path("logout", login.LogoutView.as_view()),
    path("password_reset", PasswordResetView.as_view(template_name="login/password_reset.html",
                                                     email_template_name="mails/password_reset_email.txt"),
         name="password_reset"),
    path('password_reset/done', PasswordResetDoneView.as_view(template_name='login/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>', PasswordResetConfirmView.as_view(template_name="login/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done', PasswordResetCompleteView.as_view(template_name='login/password_reset_complete.html'), name='password_reset_complete'),

    path("users/<int:pk>-<slug>", profile.ProfileView.as_view(template_name="profile/user.html"), name="users"),
    path("profile", profile.MyProfileView.as_view(template_name="profile/user.html"), name="profile"),
    path("profile/edit", profile.ChangeProfileView.as_view(template_name="profile/change.html"), name="profile_edit"),

    path('accept/<uidb64>/<token>', signup.AcceptInvitationView.as_view(), name="accept"),
] + make_path("admin", admin.site.urls)
