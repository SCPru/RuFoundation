from django.http import HttpResponse
import json
import functools


def render_json(code, o):
    return HttpResponse(json.dumps(o).encode('utf-8'), status=code, content_type='application/json')


def render_error(code, error):
    return render_json(code, {'error': error})


def restrict_method(*methods):
    def decorator(func):
        @functools.wraps(func)
        def check_method(request, *args, **kwargs):
            if request.method not in methods:
                return render_error(405, 'Некорректный метод запроса')
            return func(request, *args, **kwargs)
        return check_method
    return decorator
