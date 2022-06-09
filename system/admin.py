from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class BaseAdmin(admin.ModelAdmin):
    pass
