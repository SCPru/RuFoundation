from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse, HttpRequest
import logging
import json


class APIError(Exception):
    def __init__(self, message, code=500, *args):
        super().__init__(*args)
        self.message = message
        self.code = code


class APIView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_input = None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        try:
            return super().dispatch(*args, **kwargs)
        except APIError as e:
            return self.render_error(e.code, e.message)
        except:
            logging.error('Internal error while processing API handler:', exc_info=True)
            return self.render_error(500, 'Внутренняя ошибка сервера')

    def http_method_not_allowed(self, request, *args, **kwargs):
        # log
        super().http_method_not_allowed(request, *args, **kwargs)
        return self.render_error(405, 'Некорректный метод запроса')

    def render_json(self, code, o):
        return JsonResponse(o, status=code, safe=False)

    def render_error(self, code, error):
        return self.render_json(code, {'error': error})


def takes_json(func):
    def wrapper(self_ptr, request: HttpRequest, *args, **kwargs):
        if request.body:
            try:
                as_json = json.loads(request.body.decode('utf-8'))
                self_ptr.json_input = as_json
            except:
                raise APIError('Некорректный JSON в теле запроса')
        return func(self_ptr, request, *args, **kwargs)
    return wrapper
