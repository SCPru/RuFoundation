from django.views.generic import View
from django.http import JsonResponse, HttpRequest

from inspect import getfullargspec
from functools import lru_cache

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


def takes_url_params(func, accepted_kwargs=None):
    """Provides values from URL parameters to kwargs.
    
    Applicable only to class-based django views.
    Tries to convert URL parameter value from `str` to specified argument type.
    All function's kwargs should have devault values.
    The default argument type is `str`, unless otherwise specified.

    ```
    @takes_url_params
    def get(self, request, *, url_param_1: int=123, url_param_2: bool=True):
        ...
    ```
    """

    @lru_cache(maxsize=None)
    def get_specs(func):
        return getfullargspec(func)

    specs = get_specs(func)
    if not accepted_kwargs:
        accepted_kwargs = specs.kwonlyargs
    accepted_params = {kwarg: specs.annotations.get(kwarg, str) for kwarg in specs.kwonlyargs if kwarg in accepted_kwargs}

    def wrapper(self_ptr, request: HttpRequest, *args, **kwargs):
        if request.GET:
            try:
                for param, value in request.GET.items():
                    if param in accepted_params:
                        p_type = accepted_params[param]
                        if p_type == bool:
                            if value == 'true':
                                value = 1
                            else:
                                value = 0
                        kwargs.update({ param: p_type(value) if p_type else value })
            except:
                raise APIError('Некорректные данные в URL запроса')
        return func(self_ptr, request, *args, **kwargs)
    return wrapper