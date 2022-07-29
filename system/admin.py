from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.contrib import admin
from django.urls import path
from django import forms

from .views.signup import InviteView
from .models import User


@admin.register(User)
class AdvancedUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]["fields"] += ("bio", "avatar")
    fieldsets[0][1]["fields"] += ("type", "wikidot_username")

    inlines = []

    def get_urls(self):
        urls = super(AdvancedUserAdmin, self).get_urls()
        urls.insert(0, path("invite/", InviteView.as_view()))
        urls.insert(0, path("<id>/activate/", InviteView.as_view()))
        return urls
