from django.contrib.auth import models, admin as auth_admin
from django.urls import path
from django.contrib import admin

from .views.signup import InviteView
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile


class AdvancedUserAdmin(auth_admin.UserAdmin):
    inlines = [ProfileInline]

    def get_urls(self):
        urls = super(AdvancedUserAdmin, self).get_urls()
        urls.insert(0, path("invite/", InviteView.as_view(template_name="admin/auth/user/invite.html")))
        return urls


admin.site.unregister(models.User)
admin.site.register(models.User, AdvancedUserAdmin)
