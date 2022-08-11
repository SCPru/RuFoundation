from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.shortcuts import resolve_url
from django.conf import settings

from system.forms import UserProfileForm
from system.models import User


class ProfileView(DetailView):
    model = User
    slug_field = "username"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.get_object(self.get_queryset())
        if user.type == User.UserType.Wikidot:
            ctx['avatar'] = settings.WIKIDOT_AVATAR
            ctx['displayname'] = 'wd:'+user.wikidot_username
        else:
            ctx['avatar'] = user.get_avatar(default=settings.DEFAULT_AVATAR)
            ctx['displayname'] = user.username
        ctx['subtitle'] = ''
        if user.is_superuser:
            ctx['subtitle'] = 'Администратор сайта'
        elif user.is_staff:
            ctx['subtitle'] = 'Модератор сайта'
        return ctx

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_object(self, queryset=None):
        q = super().get_object(queryset=queryset)
        return q


class MyProfileView(LoginRequiredMixin, ProfileView):
    def get_object(self, queryset=None):
        return self.request.user


class ChangeProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm

    def get_success_url(self):
        return resolve_url("profile")

    def get_object(self, queryset=None):
        return self.request.user
