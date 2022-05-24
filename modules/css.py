def has_content():
    return True


def render(_context, _params, content=''):
    print('module css')
    code = content \
        .replace('\u00a0', ' ') \
        .replace('</style>', '\\u003c/style\\u003e')
    return '<style>%s</style>' % code
