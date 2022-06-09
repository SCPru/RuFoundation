from django.views.generic import DetailView

from system.models import User


class ProfileView(DetailView):
    model = User
    slug_field = "username"
