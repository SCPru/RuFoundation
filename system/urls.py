from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

from django.contrib import admin
from django.urls import path, URLPattern, URLResolver

from typing import Sequence, Union


_PathType = Union[URLPattern, URLResolver]


def make_path(name: str, *args, **kwargs) -> Sequence[_PathType]:
    return [
        path(f"{name}/", *args, name=name, **kwargs),
        path(name, RedirectView.as_view(url=f"{name}/", permanent=True)),
    ]


urlpatterns = []
urlpatterns += make_path("admin", admin.site.urls)
urlpatterns += make_path("login", LoginView.as_view(template_name="login.html"))
urlpatterns += make_path("logout", LogoutView.as_view(next_page="/-/login/"))
