from django.contrib import admin
from django.views.generic import TemplateView

class AdminSusActivityView(TemplateView):
    template_name = 'admin/web/user/sus.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        admin_ctx = admin.site.each_context(self.request)
        ctx.update(admin_ctx)
        return ctx