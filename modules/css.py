def has_content():
    return True


def render(_context, _params, content=''):
    code = content.replace('\u00a0', ' ').replace('<', '\\u003c')
    return '<style>%s</style>' % code
