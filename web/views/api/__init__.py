from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


class CSRFExemptMixin:
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CSRFExemptMixin, self).dispatch(*args, **kwargs)


def render_json(code, o):
    return JsonResponse(o, status=code)


def render_error(code, error):
    return render_json(code, {'error': error})
