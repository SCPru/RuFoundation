from django.contrib.auth import get_user_model


User = get_user_model()


class BotAuthTokenMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "Authorization" in request.headers:
            try:
                request.user = User.objects.get(type="bot", api_key=request.headers["Authorization"])
            except User.DoesNotExist:
                pass
        return self.get_response(request)
