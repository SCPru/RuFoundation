from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.shortcuts import resolve_url, redirect
from django.conf import settings
from django.urls import reverse

from renderer import single_pass_render
from renderer.parser import RenderContext
from web.forms import UserProfileForm
from web.models.users import User


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
        
        ctx['subtitle'] = ', '.join(user.showcase['titles'])
        ctx['bio_rendered'] = single_pass_render(user.bio, RenderContext(article=None, source_article=None, path_params=None, user=self.request.user), 'inline')
        return ctx

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        if request.user.is_staff and request.user.has_perm('roles.manage_users'):
            context['can_manage_users'] = True
            context['manage_url'] = '%s?_popup=1' % reverse(
                'admin:%s_%s_change' % (self.object._meta.app_label, self.object._meta.model_name),
                args=[self.object.pk],
            )
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        q = super().get_object(queryset=queryset)
        return q


class ChangeProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    redirect_field_name = 'to'

    def get_success_url(self):
        return "/-/profile/edit"

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.fields['bio'].label += ' (поддерживается разметка)'
        return form