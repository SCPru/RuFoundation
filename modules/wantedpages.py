import json, math

from modules.listpages import render_pagination
from renderer.utils import render_template_from_string

from web.models.articles import ExternalLink, Article
from django.db.models import Q, Value, Case, When
from django.contrib.postgres.fields import CITextField
from django.db.models.functions import Concat


def has_content():
    return False

def allow_api():
    return True

def render(context, params):
    target_page: str = params.get('target')
    category_from: str = params.get('category_from')
    category_to: str = params.get('category_to')
    limit_str: str = params.get('limit', '20')
    page_str: str = context.path_params.get('p', '1')

    all_links = Article.objects.values_list('name', 'category').annotate(full_name=Concat('category', Value(':'), 'name', output_field=CITextField())).values_list('full_name', flat=True)
    q = ExternalLink.objects.filter(link_type='link').annotate(link_to_complete=Case(When(~Q(link_to__contains=':'), then=Concat(Value('_default:'), 'link_to', output_field=CITextField())), default='link_to'))
    
    if target_page not in (None, '*'):
        q = q.filter(link_from=target_page)
    if category_from not in (None, '*'):
        q = q.annotate(link_from_complete=Case(When(~Q(link_from__contains=':'), then=Concat(Value('_default:'), 'link_from', output_field=CITextField())), default='link_from'))\
             .filter(link_from_complete__startswith=category_from)
    if category_to not in (None, '*'):
        q = q.filter(link_to_complete__startswith=category_to)
    
    q = q.exclude(link_to_complete__in=all_links)
    total_links: int = q.count()

    page: int = 1
    if page_str.isnumeric():
        page = max(1, int(page_str))
    
    limit: int = min(max(1, int(limit_str)) if limit_str.isnumeric() else 20, 500)
    offset: int = (page-1)*limit

    links = q[offset : offset + limit]

    max_page: int = max(1, int(math.ceil(total_links / limit)))
    if page > max_page:
        page = max_page

    return render_template_from_string(
                """
                <div class="w-wanted-pages"
                data-wanted-pages-path-params="{{ data_path_params }}"
                data-wanted-pages-params="{{ data_params}} ">
                {% if has_content %}
                {{ pagination }}
                    <table class="form grid" style="margin: 1em auto;">
                        <tbody>
                            <tr><th>Исходная страница</th><th>Вожделенные единицы информации</th></tr>
                            {% for record in records %}
                                <tr>
                                    <td><a href="/{{ record.link_from }}">{{ record.link_from }}</a></td>
                                    <td><a href="/{{ record.link_to }}">{{ record.link_to }}</a></td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                {{ pagination }}
                {% endif %}
                </div>
                """,
                records=links,
                has_content=total_links > 0,
                data_path_params=json.dumps(context.path_params),
                data_params=json.dumps(params),
                pagination=render_pagination(None, page, max_page) if max_page != 1 else ''
            )