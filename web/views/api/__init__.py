from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse


class APIView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def http_method_not_allowed(self, request, *args, **kwargs):
        # log
        super().http_method_not_allowed(request, *args, **kwargs)
        return self.render_error(405, 'Некорректный метод запроса')

    def render_json(self, code, o):
        return JsonResponse(o, status=code)

    def render_error(self, code, error):
        return self.render_json(code, {'error': error})
