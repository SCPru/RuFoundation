from renderer.utils import render_template_from_string


def has_content():
    return True


def render(_context, _params, content=''):
    code = content.replace('\u00a0', ' ').replace('<', '\\u003c')
    codeblock = '<div class="code w-code language-css">{{code|safe}}</div>' if _params.get("show") == "true" else ""
    return render_template_from_string('<style>{{code|safe}}</style>' + codeblock, code=code)
