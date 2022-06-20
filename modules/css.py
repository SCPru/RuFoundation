import re


def has_content():
    return True


def render(_context, _params, content=''):
    print('module css')
    code = content.replace('\u00a0', ' ')
    code = re.sub(r'<\s*/\s*style\s*>', '\\\\u003c/style\\\\u003e', code)
    return '<style>%s</style>' % code
