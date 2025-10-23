from renderer.parser import RenderContext
from renderer.utils import render_template_from_string

from web.util.css import simple_minify_css


def has_content():
    return True


def render(context: RenderContext, _params, content=''):
    content = content.replace('\u00a0', ' ')
    minified = simple_minify_css(content)
    code = minified.replace('<', '\\u003c').strip()
    # once we have a way to properly parse params, uncomment this and remove show=False
    # show = params.get('show') in ['yes', 'true']
    show = False
    context.add_css += content + '\n'
    context.computed_style += minified

    return render_template_from_string(
        """
        <div style="display: none" class="w-css-container" data-css="{{ code|safe }}"></div>
        {% if show %}
        <div class="code w-code language-css">{{ code|safe }}</div>
        {% endif %}
        """,
        code=code,
        show=show
    )
