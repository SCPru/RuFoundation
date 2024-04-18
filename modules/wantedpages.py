import json, math
from django.conf import settings

from modules.listpages import render_pagination
from web.controllers import articles
from renderer.templates import apply_template
from renderer.utils import get_boolean_param, render_template_from_string

from web.models.articles import ExternalLink, Article
from django.db.models import Q, Value, Case, When, CharField
from django.contrib.postgres.fields import CITextField
from django.db.models.functions import Concat


def has_content():
    return False

def allow_api():
    return True

def render(context, params):
    target_page: str = params.get('target', '')

    all_links = Article.objects.values_list('name', 'category').annotate(full_name=Concat('category', Value(':'), 'name', output_field=CITextField())).values_list('full_name', flat=True)
    q = ExternalLink.objects.filter(link_type='link').annotate(link_to_complete=Case(When(~Q(link_to__contains=':'), then=Concat(Value('_default:'), 'link_to', output_field=CITextField()))))
    if target_page:
        q = q.filter(link_from=target_page)
    q = q.exclude(link_to_complete__in=all_links)
    total_links: int = q.count()

    page_str: str = context.path_params.get('p', '1')

    if page_str.isnumeric():
        page: int = max(1, int(page_str))
    else:
        page: int = 1
    
    limit_str: str = params.get('limit', '20')
    limit: int = min(max(1, int(limit_str)) if limit_str.isnumeric() else 20, 500)
    offset: int = (page-1)*limit

    links = q[offset : offset + limit]

    output: str = '<table class="form grid" style="margin: 1em auto;"><tbody><tr><th>Исходная страница</th><th>Вожделенные единицы информации</th></tr>'
    output     += ''.join(map(lambda a: f'<tr><td><a href="/{a.link_from}">{a.link_from}</a></td><td><a href="/{a.link_to}">{a.link_to}</a></td></tr>', links))
    output     += '</tbody></table>'

    max_page: int = max(1, int(math.ceil(total_links / limit)))
    if page > max_page:
        page = max_page

    return render_template_from_string(
                """
                <div class="w-wanted-pages"
                data-wanted-pages-path-params="{{data_path_params}}"
                data-wanted-pages-params="{{data_params}}">
                {{pagination}}
                {{content}}
                {{pagination}}
                </div>
                """,
                content=render_template_from_string(output) if total_links > 0 else '',
                data_path_params=json.dumps(context.path_params),
                data_params=json.dumps(params),
                pagination=render_pagination(None, page, max_page) if max_page != 1 else ''
            )