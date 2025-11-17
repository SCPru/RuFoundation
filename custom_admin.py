from django.contrib.admin import AdminSite, sites
from django.urls import path
from django.contrib import admin


class CustomAdminSite(AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'web/user/sus/',
                self.admin_view(self.sus_view),
                name='custom_page'
            ),
        ]
        return custom_urls + urls

    def sus_view(self, request):
        from django.template.response import TemplateResponse
        # Your custom view logic here. Use TemplateResponse for full admin context.
        context = {
            **self.each_context(request),
            'title': 'Подозрительная активность',
            'available_apps': self.get_app_list(request)
        }
        return TemplateResponse(request, 'admin/web/user/sus.html', context)


sites.site = admin.site = CustomAdminSite('custom_admin')