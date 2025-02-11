from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View


class LoginView(TemplateResponseMixin, ContextMixin, View):
    template_name = "login/login.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not isinstance(request.user, AnonymousUser):
            to = request.GET.get('to', settings.LOGIN_REDIRECT_URL)
            return HttpResponseRedirect(redirect_to=to)
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        return self.render_to_response(context)

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        to = request.GET.get('to', settings.LOGIN_REDIRECT_URL)
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return HttpResponseRedirect(redirect_to=to)
        else:
            context.update({'error': 'Неверное имя пользователя или пароль. Пожалуйста, попробуйте снова.'})
            return self.render_to_response(context)


class LogoutView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        to = request.GET.get('to', settings.LOGIN_REDIRECT_URL)
        logout(request)
        return HttpResponseRedirect(redirect_to=to)
