from renderer.utils import get_resource


def has_content():
    return False


def render(context, _params):
    if 'src' in _params:
        context.og_image = get_resource(_params['src'], context, True)
    return ''
