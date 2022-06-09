from extra_views import UpdateWithInlinesView, InlineFormSetFactory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.shortcuts import resolve_url

from system.models import Profile, User


class ProfileView(DetailView):
    model = User
    slug_field = "username"


class MyProfileView(ProfileView):
    def get_object(self, queryset=None):
        return self.request.user


class ProfileInline(InlineFormSetFactory):
    model = Profile
    fields = ['avatar', 'bio']


class ChangeProfileView(LoginRequiredMixin, UpdateWithInlinesView):
    model = User
    inlines = [ProfileInline]
    fields = ['username', 'email']

    def get_success_url(self):
        return resolve_url("profile")

    def get_object(self, queryset=None):
        return self.request.user
