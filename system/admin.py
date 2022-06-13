from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.contrib import admin

from .views.signup import InviteView
from .models import User


@admin.register(User)
class AdvancedUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    fieldsets[1][1]["fields"] += ("bio", "avatar")
    fieldsets[0][1]["fields"] += ("type",)

    def get_urls(self):
        urls = super(AdvancedUserAdmin, self).get_urls()
        urls.insert(0, path("invite/", InviteView.as_view(template_name="admin/system/user/invite.html")))
        return urls
