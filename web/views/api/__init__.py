from django.http import HttpResponse
import json


def render_json(code, o):
    return HttpResponse(json.dumps(o).encode('utf-8'), status=code, content_type='application/json')


def render_error(code, error):
    return render_json(code, {'error': error})
