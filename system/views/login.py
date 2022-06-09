from django.views.generic import FormView
from django.shortcuts import redirect, resolve_url
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes


class PasswordResetView(FormView):
    form_class = PasswordResetForm
    email_template_name = "login/password_reset_email.txt"

    def get_success_url(self):
        return resolve_url("password_reset_done")

    def form_valid(self, form: PasswordResetForm) -> HttpResponse:
        data = form.cleaned_data['email']
        associated_users = User.objects.filter(Q(email=data))
        if associated_users.exists():
            for user in associated_users:
                subject = "Password Reset Requested"
                c = {
                    "email": user.email,
                    'domain': '127.0.0.1:8000',
                    'site_name': 'Website',
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                }
                email = render_to_string(self.email_template_name, c)
                try:
                    send_mail(subject, email, None, [user.email], fail_silently=False)
                except BadHeaderError:
                    return HttpResponse('Invalid header found.')
                return redirect(self.get_success_url())
