from renderer.utils import render_template_from_string


def has_content():
    return True


def render(_context, _params, content=''):
    code = content.replace('\u00a0', ' ').replace('<', '\\u003c')
    return render_template_from_string('<style>{{code|safe}}</style>', code=code)
