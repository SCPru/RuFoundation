from renderer.parser import LinkNode


def render(context, params):
    params = {**(context.path_params if context else {}), **params}
    if params.get('noredirect', 'false') == 'true':
        return ''
    context.redirect_to = LinkNode.filter_url(params['destination'])
    return ''
