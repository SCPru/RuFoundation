from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.contrib import admin
from django.urls import path

from .views.signup import InviteView
from .models import User


@admin.register(User)
class AdvancedUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]["fields"] += ("bio", "avatar")
    fieldsets[0][1]["fields"] += ("type",)

    actions = []

    @admin.action(description="Активировать аккаунт")
    def activate(self, request: HttpRequest, queryset: QuerySet[User]):
        if queryset.count() != 1:
            self.message_user(request, "Невозможно активировать более одного аккаунта одновременно")
            return
        user = queryset.first()
        if user.type != User.UserType.Wikidot:
            self.message_user(request, "Невозможно активировать аккаунт не перенесённый с викидота")
            return
        return InviteView.as_view()

    def get_urls(self):
        urls = super(AdvancedUserAdmin, self).get_urls()
        urls.insert(0, path("invite/", InviteView.as_view()))
        return urls
