def has_content():
    return True


def render(context, _params, content=''):
    content = content.replace('\u00a0', ' ').replace('<', '\\u003c')
    if content:
        context.og_description = content
    return ''
