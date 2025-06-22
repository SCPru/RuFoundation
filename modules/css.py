from renderer.utils import render_template_from_string


def has_content():
    return True


def render(context, _params, content=''):
    content = content.replace('\u00a0', ' ')
    code = content.replace('<', '\\u003c')
    # once we have a way to properly parse params, uncomment this and remove show=False
    # show = params.get('show') in ['yes', 'true']
    show = False
    context.add_css += content + '\n'
    return render_template_from_string(
        """
        <style>{{code|safe}}</style>
        {% if show %}
        <div class="code w-code language-css">{{code|safe}}</div>
        {% endif %}
        """,
        code=code,
        show=show
    )
