from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, BadHeaderError
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.shortcuts import redirect, resolve_url
from django.http import HttpResponseBadRequest
from django.contrib.auth.models import User
from django.views.generic import FormView
from django.contrib.auth import login
from django.contrib.admin import site
from django.contrib import messages
from django.conf import settings


from system.forms import InviteForm, CreateAccountForm


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)


account_activation_token = TokenGenerator()


@method_decorator(staff_member_required, name='dispatch')
class InviteView(FormView):
    form_class = InviteForm
    email_template_name = "mails/invite_email.txt"

    def get_context_data(self, **kwargs):
        context = super(InviteView, self).get_context_data(**kwargs)
        context["title"] = "Инвайт пользователя"
        context.update(site._wrapped.each_context(self.request))
        return context

    def get_success_url(self):
        return resolve_url("admin:index")

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.is_active = False
            user.save()
            subject = f"Приглашение на {settings.WEBSITE_NAME}"
            c = {
                "email": user.email,
                'domain': "scpfoundation.net",
                'site_name': settings.WEBSITE_NAME,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                'token': account_activation_token.make_token(user),
                'protocol': 'https',
            }
            content = render_to_string(self.email_template_name, c)
            try:
                send_mail(subject, content, None, [user.email], fail_silently=False)
                messages.success(self.request, "Приглашение успешно отправлено")
            except BadHeaderError:
                messages.error(self.request, "Неправильный заголовок")
        else:
            messages.error(self.request, "Данный email уже привязан к участнику сайта")

        return redirect(self.get_success_url())


class ActivateView(FormView):
    form_class = CreateAccountForm
    success_url = "/"

    def __init__(self, *args, **kwargs):
        super(ActivateView, self).__init__(*args, **kwargs)
        self.user = None

    def get_user(self):
        try:
            uid = force_str(urlsafe_base64_decode(self.kwargs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        return user

    def form_valid(self, form):
        self.user = self.get_user()
        if self.user is not None and account_activation_token.check_token(self.user, self.kwargs["token"]):
            self.user.username = form.cleaned_data["username"]
            self.user.set_password(form.cleaned_data["password"])
            self.user.is_active = True
            self.user.save()
            login(self.request, self.user, backend="django.contrib.auth.backends.ModelBackend")
            return super(ActivateView, self).form_valid(form)
        return HttpResponseBadRequest("Invalid user token")

