from django.http import HttpRequest

from shared_data import shared_users
from . import APIView


class AllUsersView(APIView):
    def get(self, request: HttpRequest):
        return self.render_json(200, shared_users.get_all_users())