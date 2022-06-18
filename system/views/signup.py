from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, BadHeaderError
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.shortcuts import redirect, resolve_url
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from django.views.generic import FormView
from django.contrib.auth import login
from django.contrib.admin import site
from django.contrib import messages


from system.forms import InviteForm, CreateAccountForm
from web.models.sites import get_current_site

User = get_user_model()


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + str(user.is_active)


account_activation_token = TokenGenerator()


@method_decorator(staff_member_required, name='dispatch')
class InviteView(FormView):
    form_class = InviteForm
    email_template_name = "mails/invite_email.html"

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
        site = get_current_site()
        if created:
            user.is_active = False
            user.username = 'user-%d' % user.id
            user.save()
            subject = f"Приглашение на {site.title}"
            c = {
                "email": user.email,
                'domain': self.request.get_host(),
                'site_name': site.title,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                'token': account_activation_token.make_token(user),
                'protocol': self.request.scheme,
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

    def get_success_url(self):
        return resolve_url("profile_edit")

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

