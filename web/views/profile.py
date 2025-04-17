from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.shortcuts import resolve_url, redirect
from django.conf import settings

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
        ctx['subtitle'] = ''
        if not user.is_active:
            ctx['subtitle'] = 'Неактивен' if user.type == User.UserType.Wikidot else 'Заблокирован'
        elif user.is_superuser:
            ctx['subtitle'] = 'Администратор сайта'
        elif user.is_staff:
            ctx['subtitle'] = 'Модератор сайта'
        elif user.is_editor:
            ctx['subtitle'] = 'Участник'
        else:
            ctx['subtitle'] = 'Читатель'
        if user.visual_group:
            ctx['subtitle'] += ' (%s)' % user.visual_group.name
        ctx['bio_rendered'] = single_pass_render(user.bio, RenderContext(article=None, source_article=None, path_params=None, user=self.request.user), 'inline')
        return ctx

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_object(self, queryset=None):
        q = super().get_object(queryset=queryset)
        return q


class MyProfileView(LoginRequiredMixin, ProfileView):
    def get(self, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return redirect('/')
        else:
            return redirect('/-/users/%d-%s' % (obj.id, obj.username))

    def get_object(self, queryset=None):
        return self.request.user


class ChangeProfileView(LoginRequiredMixin, UpdateView):
    form_class = UserProfileForm
    redirect_field_name = 'to'

    def get_success_url(self):
        return resolve_url("profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.fields['bio'].label += ' (поддерживается разметка)'
        return form