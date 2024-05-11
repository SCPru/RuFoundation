import json, math

from modules.listpages import param, query_pages, render_pagination
from modules.listpages.params import ListPagesParams
from renderer.utils import render_template_from_string

from web.controllers import articles
from web.models.articles import ExternalLink, Article
from django.db.models import Q, Value as V, Case, When, Subquery, OuterRef
from django.contrib.postgres.fields import CITextField
from django.db.models.functions import Concat, Substr, StrIndex

def has_content():
    return False

def allow_api():
    return True

def render(context, params):
    if 'category_from' in params and 'category' not in params:
        params['category'] = params['category_from']
    if 'limit' in params:
        params['limit'] = None
    if 'offset' in params:
        params['offset'] = None

    category_to   : str = params.get('category_to', '*')
    per_page_str  : str = params.get('perpage')
    page_str      : str = context.path_params.get('p')

    parsed_params = ListPagesParams(context.article, context.user, {
        'category': category_to,
        'perpage' : per_page_str
    },
    {
        'p': page_str
    })

    filtered_pages, _, _, _, _ = query_pages(context.article, params, context.user, allow_pagination=False)

    if isinstance(filtered_pages, list):
        filtered_pages_names = [page.full_name if page.category != '_default' else f'{page.category}:{page.name}' for page in filtered_pages]
    else:
        filtered_pages_names = filtered_pages.annotate(full_name=Concat('category', V(':'), 'name', output_field=CITextField())).values('full_name')
    
    all_articles = Article.objects.values('name', 'category', 'title') \
      .annotate(full_name=Concat('category', V(':'), 'name', output_field=CITextField()))
    q = ExternalLink.objects.filter(link_type='link') \
      .annotate(link_from_complete=Case(When(~Q(link_from__contains=':'), then=Concat(V('_default:'), 'link_from', output_field=CITextField())), default='link_from')) \
      .filter(link_from_complete__in=filtered_pages_names) \
      .annotate(link_to_complete=Case(When(~Q(link_to__contains=':'), then=Concat(V('_default:'), 'link_to', output_field=CITextField())), default='link_to')) \

    q = q.exclude(link_to_complete__in=all_articles.values('full_name'))

    for p in parsed_params.params:
        match p:
            case param.Category(allowed=allowed, not_allowed=not_allowed):
                q = q.annotate(category_to=Case(When(~Q(link_to__contains=':'), then=V('_default')), default=Substr('link_to', 1, StrIndex('link_to', V(':')) - 1)))
                if allowed:
                    q = q.filter(category_to__in=allowed)
                if not_allowed:
                    q = q.filter(~Q(category_to__in=not_allowed))

            case param.Pagination(page=page, per_page=per_page):
                    page = page
                    per_page = min(per_page, 250)
    
    total_links: int = q.count()

    offset: int = (page - 1) * per_page
    links = q[offset : offset + per_page]

    links = links.annotate(title=Subquery(all_articles.filter(full_name=OuterRef('link_from_complete')).values('title')))

    max_page: int = max(1, int(math.ceil(total_links / per_page)))
    if page > max_page:
        page = max_page

    return render_template_from_string(
                """
                <div class="w-wanted-pages"
                data-wanted-pages-path-params="{{ data_path_params }}"
                data-wanted-pages-params="{{ data_params }}"
                data-wanted-pages-page-id="{{ data_page_id }}">
                {{ pagination }}
                <table class="form grid" style="margin: 1em auto;">
                    <tbody>
                        <tr><th>Исходная страница</th><th>Отсутствующие ссылки</th></tr>
                        {% for record in records %}
                        <tr>
                            <td><a href="/{{ record.link_from }}">{{ record.title }}</a></td>
                            <td><a href="/{{ record.link_to }}" class="newpage">{{ record.link_to }}</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {{ pagination }}
                </div>
                """,
                records=links,
                data_path_params=json.dumps(context.path_params),
                data_params=json.dumps(params),
                data_page_id=articles.get_full_name(context.article) or '',
                pagination=render_pagination(None, page, max_page) if max_page != 1 else ''
            )