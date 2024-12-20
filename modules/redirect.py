from renderer.utils import validate_url, get_boolean_param


def render(context, params):
    params = {**(context.path_params if context else {}), **params}
    if get_boolean_param(params, 'noredirect'):
        return ''
    context.redirect_to = validate_url(params['destination'])
    return ''
