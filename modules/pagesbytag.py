import re

from django.db.models import Count, Q

from renderer.utils import render_template_from_string
from . import ModuleError
from web.controllers.articles import get_tag
from web.models.articles import Tag


def render(context, params):
    for k in context.path_params:
        params[k] = context.path_params[k]

    if 'tag' not in params:
        return ''

    tag = get_tag(params["tag"], create=False)

    # find articles by tag
    try:
        articles = tag.articles.order_by('title')
    except (AttributeError, Tag.DoesNotExist):
        return ''

    articles = [{'full_name': x.full_name, 'title': x.title or x.full_name} for x in articles]

    return render_template_from_string(
        """
        <a name="pages"></a>
        <h2>Список страниц, помеченных тегом <em>{{ tag.name }}</em>{% if not tag.category.is_default %} из категории <em>{{ tag.category.name }}</em>{% endif %}:</h2>
        <div id="tagged-pages-list" class="pages-list">
            {% for article in articles %}
                <div class="pages-list-item">
                    <div class="title">
                        <a href="/{{ article.full_name }}">{{ article.title }}</a>
                    </div>
                </div>
            {% endfor %}
        </div>
        """,
        tag=tag,
        articles=articles
    )
