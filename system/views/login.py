from django.conf import settings
from django.views.generic import FormView
from django.shortcuts import redirect, resolve_url
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes


class PasswordResetView(FormView):
    form_class = PasswordResetForm
    email_template_name = "mails/password_reset_email.txt"

    def get_success_url(self):
        return resolve_url("password_reset_done")

    def form_valid(self, form: PasswordResetForm) -> HttpResponse:
        data = form.cleaned_data['email']
        user = User.objects.get(email=data)
        if user.exists():
            subject = "Password Reset Requested"
            c = {
                "email": user.email,
                'domain': "scpfoundation.net",
                'site_name': settings.WEBSITE_NAME,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                'token': default_token_generator.make_token(user),
                'protocol': 'https',
            }
            content = render_to_string(self.email_template_name, c)
            try:
                send_mail(subject, content, None, [user.email], fail_silently=False)
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect(self.get_success_url())
