from django.http import HttpRequest

from shared_data import shared_users
from . import APIView, APIError

from web.models import ActionLogEntry


class AllUsersView(APIView):
    def get(self, request: HttpRequest):
        return self.render_json(200, shared_users.get_all_users())


class AdminSusActivityView(APIView):
    def get(self, request: HttpRequest):
        if not request.user.has_perm('roles.view_sensetive_info'):
            raise APIError('Недостаточно прав', 403)
        items = list()
        for logentry in ActionLogEntry.objects.prefetch_related('user').distinct('user', 'origin_ip'):
            items.append({
                'user': {
                    'id': logentry.user.id,
                    'name': logentry.user.username,
                },
                'ip': logentry.origin_ip
            })
        return self.render_json(200, items)
