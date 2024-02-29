from renderer.utils import filter_url, get_boolean_param


def render(context, params):
    params = {**(context.path_params if context else {}), **params}
    if get_boolean_param(params, 'noredirect'):
        return ''
    context.redirect_to = filter_url(params['destination'])
    return ''
