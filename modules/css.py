from renderer.parser import RenderContext
from renderer.utils import get_boolean_param, render_template_from_string

from web.util.css import simple_minify_css


def has_content():
    return True


def render(context: RenderContext, params, content=''):
    params = {**(context.path_params if context else {}), **params}
    inline = get_boolean_param(params, 'inline')

    content = content.replace('\u00a0', ' ')
    minified = simple_minify_css(content)
    code = content.replace('<', '\\u003c').strip()
    # once we have a way to properly parse params, uncomment this and remove show=False
    # show = params.get('show') in ['yes', 'true']
    show = False
    context.add_css += content + '\n'
    if not inline:
        context.computed_style += '\n'+minified

    return render_template_from_string(
        """
        {% if inline %}
            <style>{{ code|safe }}</style>
        {% endif %}
        {% if show %}
            <div class="code w-code language-css">{{ code|safe }}</div>
        {% endif %}
        """,
        code=code,
        show=show,
        inline=inline
    )
