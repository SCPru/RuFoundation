from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import AbstractUser as _UserType
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponseRedirect
from django.contrib.auth import login
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View

import re

from web.models.users import UsedToken
from .invite import account_activation_token
from web.events import EventBase


User = get_user_model()


class OnUserSignUp(EventBase, name='on_user_signup'):
    request: HttpRequest
    user: _UserType

class AcceptInvitationView(TemplateResponseMixin, ContextMixin, View):
    template_name = "signup/accept.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_user(self):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def get(self, request, *args, **kwargs):
        if not isinstance(request.user, AnonymousUser):
            return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        user = self.get_user()
        if UsedToken.is_used(self.kwargs['token']) or not account_activation_token.check_token(user, self.kwargs["token"]):
            context.update({'error': 'Некорректное приглашение.', 'error_fatal': True})
            return self.render_to_response(context)
        if user.type == User.UserType.Wikidot:
            context.update({'is_wikidot': True, 'username': user.wikidot_username})
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        user = self.get_user()
        if UsedToken.is_used(self.kwargs['token']) or not account_activation_token.check_token(user, self.kwargs['token']):
            context.update({'error': 'Некорректное приглашение.', 'error_fatal': True})
            return self.render_to_response(context)
        if user.type == User.UserType.Wikidot:
            username = user.wikidot_username
            context.update({'is_wikidot': True})
        else:
            username = request.POST.get('username', '').strip()
        context.update({'username': username})
        password1 = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        # check if username is not valid
        if not re.match(r"^[\w.-]+\Z", username, re.ASCII):
            context.update({'error': 'Некорректное имя пользователя. Разрешённые символы: A-Z, a-z, 0-9, -, _.'})
            return self.render_to_response(context)
        # check if user already exists
        user_exists = User.objects.filter(username__iexact=username)
        wd_user_exists = User.objects.filter(wikidot_username__iexact=username)
        if (user_exists and user_exists[0] != user) or (wd_user_exists and wd_user_exists[0] != user):
            context.update({'error': 'Выбранное имя пользователя уже используется.'})
            return self.render_to_response(context)
        if not password1:
            context.update({'error': 'Пароль должен быть указан.'})
            return self.render_to_response(context)
        if password1 != password2:
            context.update({'error': 'Введенные пароли не совпадают.'})
            return self.render_to_response(context)
        if user.type != User.UserType.Wikidot:
            user.username = username
        else:
            user.username = user.wikidot_username
            user.type = User.UserType.Normal
        user.set_password(password1)
        user.is_active = True
        user.save()
        UsedToken.mark_used(self.kwargs['token'], is_case_sensitive=True)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        OnUserSignUp(request, user).emit()
        return HttpResponseRedirect(redirect_to=settings.LOGIN_REDIRECT_URL)

