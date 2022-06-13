from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.contrib import admin

from .views.signup import InviteView
from .models import User


@admin.register(User)
class AdvancedUserAdmin(UserAdmin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = super(AdvancedUserAdmin, self).get_fieldsets(request, obj)
        # fs now contains [(None, {'fields': fields})], do with it whatever you want
        fieldsets[1][1]["fields"] += ("bio", "avatar")
        return fieldsets

    def get_urls(self):
        urls = super(AdvancedUserAdmin, self).get_urls()
        urls.insert(0, path("invite/", InviteView.as_view(template_name="admin/system/user/invite.html")))
        return urls
