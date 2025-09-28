import json
import urllib.parse
import math
import re

from django.utils.safestring import SafeString

import renderer
from renderer.templates import apply_template
from renderer.utils import render_user_to_text, render_template_from_string, get_boolean_param
from renderer.parser import RenderContext
from web.controllers import articles
from web.models.users import User
from web.models.articles import Article, ArticleLogEntry
from web.models.settings import Settings
from django.db.models import Q, Value as V, F, Count, Sum, Avg, Case, When, CharField, IntegerField, FloatField
from django.db.models.functions import Concat, Random, Coalesce, Round, Cast
from web import threadvars

from .params import ListPagesParams
from . import param

from web.util.lazy_dict import LazyDict


def has_content():
    return True


def allow_api():
    return True


def api_get(context, _params):
    return {"pages": [page.full_name for page in query_pages(context.article, _params, context.user, context.path_params, False)[0]]}


def render_date(date, format='%H:%M %d.%m.%Y'):
    if not date:
        return 'n/a'
    return render_template_from_string('<span class="odate w-date" style="display: inline" data-timestamp="{{ timestamp }}" data-format="{{ format }}">{{ serverside }}</span>', timestamp=int(date.timestamp()*1000), format=format, serverside=date.strftime(format))


def render_var(var, page_vars, page):
    if var in page_vars:
        v = page_vars[var]
        return v() if callable(v) else v
    if var.startswith('created_at|'):
        format = var[11:].strip()
        try:
            return '[[date %s format="%s"]]' % (int(page.created_at.timestamp()), format)
        except:
            return page_vars['created_at']
    if var.startswith('updated_at|'):
        format = var[11:].strip()
        try:
            return '[[date %s format="%s"]]' % (int(page.updated_at.timestamp()), format)
        except:
            return page_vars['updated_at']
    return None

def get_page_vars(page: Article):
    if page is None:
        return dict()

    current_user = threadvars.get('current_user', None)
    if not isinstance(current_user, User):
        current_user = None
    
    updated_by = None

    def get_updated_by():
        nonlocal updated_by
        if not updated_by:
            updated_by = articles.get_latest_log_entry(page).user

        return updated_by
    
    rating_cache = {}
    def get_rating(key: str):
        if not rating_cache:
            _, votes, popularity, _ = articles.get_rating(page)
            rating_cache['votes'] = votes
            rating_cache['popularity'] = popularity
        return rating_cache[key]
    
    page_vars = LazyDict({
        'name': lambda: page.name,
        'category': lambda: page.category,
        'fullname': lambda: articles.get_full_name(page),
        'title': lambda: page.title,
        'title_linked': lambda: '[[[%s|]]]' % (articles.get_full_name(page)),
        'link': lambda: '/%s' % page.title,  # temporary, must be full page URL based on hostname
        'content': lambda: articles.get_latest_source(page),
        'rating': lambda: articles.get_formatted_rating(page),
        'rating_votes': lambda: str(get_rating('votes')),
        'current_user_voted': lambda: 'True' if page.votes.filter(user=current_user).exists() else 'False',
        'popularity': lambda: str(get_rating('popularity')),
        'revisions': lambda: str(len(ArticleLogEntry.objects.filter(article=page))),
        'created_by': lambda: render_user_to_text(page.author),
        'created_by_linked': lambda: ('[[*user %s]]' % page.author.username) if page.author and 'username' in page.author.__dict__ else render_user_to_text(page.author),
        'updated_by': lambda: render_user_to_text(get_updated_by()),
        'updated_by_linked': lambda: ('[[*user %s]]' % get_updated_by().username) if get_updated_by() and 'username' in get_updated_by().__dict__ else render_user_to_text(get_updated_by()),
        # content{n} = content sections are not supported yet
        # preview and preview(n) = first characters of the page are not supported yet
        # summary = wtf is this?
        'tags': lambda: ', '.join(articles.get_tags(page)),
        'tags_linked': lambda: ', '.join(('[/system:page-tags/tag/%s %s]' % (urllib.parse.quote(tag, safe=''), tag)) for tag in articles.get_tags(page)),
        # _tags, _tags_linked, _tags_linked|link_prefix = not yet
        # form_data{name}, form_raw{name}, form_label{name}, form_hint{name} = never ever
        'created_at': lambda: '[[date %d]]' % int(page.created_at.timestamp()),
        'updated_at': lambda: '[[date %d]]' % int(page.updated_at.timestamp()),
        # commented_at, commented_by, commented_by_unix, commented_by_id, commented_by_linked = not yet
    })

    if page.parent_id is not None:
        page_vars['parent_name'] = lambda: page.parent.name
        page_vars['parent_category'] = lambda: page.parent.category
        page_vars['parent_fullname'] = lambda: articles.get_full_name(page.parent)
        page_vars['parent_title'] = lambda: page.parent.title
        page_vars['parent_title_linked'] = lambda: '[[[%s|%s]]]' % (articles.get_full_name(page.parent), page.parent.title)

    return page_vars

def page_to_listpages_vars(page: Article, template, index, total, page_vars=None):
    if page_vars is None:
        page_vars = get_page_vars(page)

    page_vars['index'] = lambda: str(index)
    page_vars['total'] = lambda: str(total)
    
    template = apply_template(template, lambda name: render_var(name, page_vars, page))
    return template


def query_pages(article, params, viewer=None, path_params=None, allow_pagination=True, always_query=False):
    if path_params is None:
        path_params = {}

    # legacy param aliases
    if 'created_at' not in params and 'date' in params:
        params['created_at'] = params['date']

    pagination_page = 1
    pagination_total_pages = 1
    page_index = 0

    parsed_params = ListPagesParams(article, viewer, params, path_params)

    if not parsed_params.is_valid():
        if always_query:
            return Article.objects.none(), 0, 1, 1, 0
        return [], 0, 1, 1, 0

    article_param = parsed_params.get_type(param.Article)
    if article_param:
        if always_query:
            q = Article.objects.filter(id=article_param[0].article.id)
            return q, 0, 1, 1, 1
        return [article_param[0].article], 0, 1, 1, 1

    full_name_param = parsed_params.get_type(param.FullName)
    if full_name_param:
        if always_query:
            category, name = articles.get_name(full_name_param)
            q = Article.objects.filter(category=category, name=name)
            return q, 0, 1, 1, int(q.count() > 0)
        article = articles.get_article(full_name_param[0].full_name)
        if article:
            return [article], 0, 1, 1, 1
        else:
            return [], 0, 1, 1, 0

    prefetch_related = []
    select_related = []

    has_rating = parsed_params.has_type(param.Rating)
    has_votes = parsed_params.has_type(param.Votes)
    has_popularity = parsed_params.has_type(param.Popularity)

    sorting_param = parsed_params.get_type(param.Sort)
    if sorting_param:
        sorting_param = sorting_param[0]
        if sorting_param.column == 'rating':
            has_rating = True
        if sorting_param.column == 'votes':
            has_votes = True
        if sorting_param.column == 'popularity':
            has_votes = True
            has_popularity = True

    has_tags = parsed_params.has_type(param.Tags)
    has_parent = parsed_params.has_type(param.Parent) or parsed_params.has_type(param.NotParent)

    if has_rating or has_votes or has_popularity:
        prefetch_related.append('votes')

    if has_tags:
        prefetch_related.append('tags')

    if has_parent:
        select_related.append('parent')

    q = Article.objects.select_related(*select_related)
    q = q.prefetch_related(*prefetch_related).distinct()

    # detect required annotations and annotate if needed
    if has_votes:
        q = q.annotate(num_votes=Count('votes', distinct=True))

    if has_rating or has_popularity:
        requested_category = '_default'
        category_param = parsed_params.get_type(param.Category)
        if category_param and category_param[0].allowed:
            requested_category = category_param[0].allowed[0]

        rating_func = F('id')

        obj_settings = Article(name='_tmp', category=requested_category or '_default').get_settings()
        popularity_filter = V(True)
        if obj_settings.rating_mode == Settings.RatingMode.UpDown:
            rating_func = Coalesce(Sum('votes__rate'), 0)
            popularity_filter = Q(votes__rate__gt=0)
        elif obj_settings.rating_mode == Settings.RatingMode.Stars:
            rating_func = Coalesce(Avg('votes__rate'), 0.0)
            popularity_filter = Q(votes__rate__gte=3.0)


        if has_rating:
            q = q.annotate(rating=rating_func)
        if has_popularity:
            q = q.annotate(num_votes_above_popularity=Count('votes', filter=popularity_filter, distinct=True))
            q = q.annotate(popularity=Case(
                When(Q(num_votes__gt=0), then=Round((Cast(F('num_votes_above_popularity'), FloatField()) / Cast(F('num_votes'), FloatField())) * 100, output_field=IntegerField())),
                When(Q(num_votes=0), then=0))
            )

    requested_offset = 0
    requested_limit = None
    requested_page = 1
    requested_per_page = 20

    for p in parsed_params.params:
        match p:
            case param.Type(type='normal'):
                q = q.filter(~Q(name__startswith='_'))
            case param.Type(type='hidden'):
                q = q.filter(Q(name__startswith='_'))
            case param.Name(name=name):
                q = q.filter(name=name)
            case param.NamePrefix(prefix=prefix):
                q = q.filter(name__startswith=prefix)
            case param.NoTags():
                q = q.filter(tags__isnull=True)
            case param.ExactTags(tags=tags):
                q = q.filter(tags__in=tags).annotate(num_tags=Count('tags', distinct=True)).filter(num_tags=len(tags))
            case param.Tags(required=required, present=present, absent=absent):
                if required:
                    q = q.filter(tags__in=required).annotate(num_required_tags=Count('tags', distinct=True, filter=Q(tags__in=required))).filter(num_required_tags=len(required))
                if present:
                    q = q.filter(tags__in=present)
                if absent:
                    q = q.filter(~Q(tags__in=absent))
            case param.Category(allowed=allowed, not_allowed=not_allowed):
                if allowed:
                    q = q.filter(category__in=allowed)
                if not_allowed:
                    q = q.filter(~Q(category__in=not_allowed))
            case param.Parent(parent=parent):
                q = q.filter(parent=parent)
            case param.NotParent(parent=parent):
                q = q.filter(~Q(parent=parent))
            case param.CreatedBy(user=user):
                q = q.filter(author=user)
            # ---- start CreatedAt
            case param.CreatedAt(type='range', start=start, end=end):
                q = q.filter(created_at__gte=start, created_at__lte=end)
            case param.CreatedAt(type='exclude_range', start=start, end=end):
                q = q.filter(Q(created_at__lt=start) | Q(created_at__gt=end))
            case param.CreatedAt(type='lt', start=start):
                q = q.filter(created_at__lt=start)
            case param.CreatedAt(type='lte', start=start):
                q = q.filter(created_at__lte=start)
            case param.CreatedAt(type='gt', end=end):
                q = q.filter(created_at__gt=end)
            case param.CreatedAt(type='gte', end=end):
                q = q.filter(created_at__gte=end)
            # ---- end CreatedAt
            # ---- start Rating
            case param.Rating(type='eq', rating=rating):
                q = q.filter(rating=rating)
            case param.Rating(type='ne', rating=rating):
                q = q.filter(~Q(rating=rating))
            case param.Rating(type='lt', rating=rating):
                q = q.filter(rating__lt=rating)
            case param.Rating(type='lte', rating=rating):
                q = q.filter(rating__lte=rating)
            case param.Rating(type='gt', rating=rating):
                q = q.filter(rating__gt=rating)
            case param.Rating(type='gte', rating=rating):
                q = q.filter(rating__gte=rating)
            # ---- end Rating
            # ---- start Votes
            case param.Votes(type='eq', votes=votes):
                q = q.filter(num_votes=votes)
            case param.Votes(type='ne', votes=votes):
                q = q.filter(~Q(num_votes=votes))
            case param.Votes(type='lt', votes=votes):
                q = q.filter(num_votes__lt=votes)
            case param.Votes(type='lte', votes=votes):
                q = q.filter(num_votes__lte=votes)
            case param.Votes(type='gt', votes=votes):
                q = q.filter(num_votes__gt=votes)
            case param.Votes(type='gte', votes=votes):
                q = q.filter(num_votes__gte=votes)
            # ---- end Votes
            # ---- start Popularity
            case param.Popularity(type='eq', popularity=popularity):
                q = q.filter(popularity=popularity)
            case param.Popularity(type='ne', popularity=popularity):
                q = q.filter(~Q(popularity=popularity))
            case param.Popularity(type='lt', popularity=popularity):
                q = q.filter(popularity__lt=popularity)
            case param.Popularity(type='lte', popularity=popularity):
                q = q.filter(popularity__lte=popularity)
            case param.Popularity(type='gt', popularity=popularity):
                q = q.filter(popularity__gt=popularity)
            case param.Popularity(type='gte', popularity=popularity):
                q = q.filter(popularity__gte=popularity)
            # ---- end Popularity
            case param.Sort(column=column, direction=direction):
                allowed_sort_columns = {
                    'created_at': F('created_at'),
                    'created_by': F('author'),
                    'name': F('name'),
                    'title': F('title'),
                    'updated_at': F('updated_at'),
                    'fullname': F('complete_full_name'),
                    'rating': F('rating'),
                    'votes': F('num_votes'),
                    'popularity': F('popularity'),
                    'random': Random(),
                }
                if column not in allowed_sort_columns:
                    column = 'created_at'
                    direction = 'desc'
                # asc/desc is a function call on DB val, e.g. F('popularity').asc(), so we use getattr here
                q = q.order_by(getattr(allowed_sort_columns[column], direction)())
            case param.Offset(offset=offset):
                requested_offset = offset
            case param.Limit(limit=limit):
                requested_limit = limit
            case param.Pagination(page=page, per_page=per_page):
                requested_page = page
                requested_per_page = min(per_page, 250)

    if requested_limit is not None:
        q = q[requested_offset:requested_offset + requested_limit]
    else:
        q = q[requested_offset:]

    total_pages = q.count()

    if allow_pagination:
        q = q[(requested_page - 1) * requested_per_page:requested_page * requested_per_page]
        page_index += (requested_page - 1) * requested_page
        pagination_page = requested_page
        pagination_total_pages = int(math.ceil(total_pages / requested_per_page))

    pages = q

    return pages, page_index, pagination_page, pagination_total_pages, total_pages


def render_pagination(base_path, pagination_page, pagination_total_pages):
    if pagination_total_pages > 1:
        around_pages = 2
        left_from = 1
        left_to = left_from + 1
        if pagination_page < (around_pages * 2 + 1):
            left_to = around_pages + 1
        if left_to > pagination_total_pages - 1:
            left_to = pagination_total_pages - 1
        right_to = pagination_total_pages
        right_from = max(left_to + 1, right_to - 1)
        if pagination_page > (right_to - (around_pages * 2 + 1)):
            right_from = max(left_to + 1, pagination_total_pages - (around_pages + 1))
        center_from = max(left_to + 1, pagination_page - around_pages)
        center_to = min(right_from - 1, pagination_page + around_pages)
        return render_template_from_string(
            """
            <div class="pager">
                <span class="pager-no">страница&nbsp;{{page}}&nbsp;из&nbsp;{{total_pages}}</span>
                {% if show_prev_page %}
                    <span class="target"><a href="{%if base_path%}{{base_path}}/p/{{prev_page}}{% else %}#{%endif%}" data-pagination-target="{{prev_page}}">&laquo;&nbsp;предыдущая</a></span>
                {% endif %}
                {% for p in left_pages %}
                    {% if page == p %}
                        <span class="1 target current">{{p}}</span>
                    {% else %}
                        <span class="1 target"><a href="{%if base_path%}{{base_path}}/p/{{p}}{% else %}#{%endif%}" data-pagination-target="{{p}}">{{p}}</a></span>
                    {% endif %}
                {% endfor %}
                {% if show_left_dots %}
                    <span class="dots">...</span>
                {% endif %}
                {% for p in center_pages %}
                    {% if page == p %}
                        <span class="2 target current">{{p}}</span>
                    {% else %}
                        <span class="2 target"><a href="{%if base_path%}{{base_path}}/p/{{p}}{% else %}#{%endif%}" data-pagination-target="{{p}}">{{p}}</a></span>
                    {% endif %}
                {% endfor %}
                {% if show_right_dots %}
                    <span class="dots">...</span>
                {% endif %}
                {% for p in right_pages %}
                    {% if page == p %}
                        <span class="3 target current">{{p}}</span>
                    {% else %}
                        <span class="3 target"><a href="{%if base_path%}{{base_path}}/p/{{p}}{% else %}#{%endif%}" data-pagination-target="{{p}}">{{p}}</a></span>
                    {% endif %}
                {% endfor %}
                {% if show_next_page %}
                    <span class="target"><a href="{%if base_path%}{{base_path}}/p/{{next_page}}{% else %}#{%endif%}" data-pagination-target="{{next_page}}">следующая&nbsp;&raquo;</a></span>
                {% endif %}
            </div>
            """,
            left_pages=range(left_from, left_to+1),
            center_pages=range(center_from, center_to+1),
            right_pages=range(right_from, right_to+1),
            show_left_dots=(center_from > left_to + 1),
            show_right_dots=(center_to < right_from - 1),
            show_prev_page=pagination_page > 1,
            prev_page=pagination_page-1,
            show_next_page=pagination_page < pagination_total_pages,
            next_page=pagination_page+1,
            base_path=base_path,
            page=pagination_page,
            total_pages=pagination_total_pages
        )
    return ''


def render(context: RenderContext, params, content=None):
    with threadvars.context():
        content = (content or '').strip()

        # do url params
        for k, v in params.items():
            if v[:5].lower() == '@url|':
                default = v[5:]
                if k in context.path_params:
                    params[k] = context.path_params[k]
                else:
                    params[k] = default

        prepend = params.get('prependline', '')
        append = params.get('appendline', '')
        separate = get_boolean_param(params, 'separate', True)
        wrapper = get_boolean_param(params, 'wrapper', True)

        if content:
            selection = re.match(r'(?:.*\s*(\[\[head]]\n?.(?P<head>.*?).\[\[/head]])|)(?:.*\s*(\[\[body]]\n?.(?P<body>.*?).\[\[/body]])|)(?:.*\s*(\[\[foot]]\n?.(?P<foot>.*?).\[\[/foot]])|)', content, re.S | re.I | re.M)
            if selection:
                if selection.group("head"):
                    prepend = selection.group("head")
                if selection.group("body"):
                    content = selection.group("body")
                if selection.group("foot"):
                    append = selection.group("foot")

        pages, page_index, pagination_page, pagination_total_pages, total_pages = query_pages(context.article, params, context.user, context.path_params)

        pages = list(pages)
        if get_boolean_param(params, 'reverse', False):
            pages = reversed(pages)

        output = SafeString()
        common_context = context.clone_with(source_article=context.article)

        if separate:
            if prepend:
                output += renderer.single_pass_render(prepend+'\n', common_context)
            for page in pages:
                page_index += 1
                page_content = page_to_listpages_vars(page, content, page_index, total_pages)
                cc = common_context.clone_with(article=page, source_article=page)
                output += renderer.single_pass_render(page_content+'\n', cc)
                common_context.merge(cc)
            if append:
                output += renderer.single_pass_render(append, common_context)
        else:
            source = ''
            if prepend:
                source += prepend+'\n'
            for page in pages:
                page_index += 1
                page_content = page_to_listpages_vars(page, content, page_index, total_pages)
                source += page_content+'\n'
            source += append
            output += renderer.single_pass_render(source, common_context)

        context.merge(common_context)

        if wrapper:
            if context.article:
                base_path = '/%s' % context.article.full_name
                for k, v in context.path_params.items():
                    if k != 'p':
                        base_path += '/%s/%s' % (urllib.parse.quote_plus(str(k)), urllib.parse.quote_plus(str(v)))
            else:
                base_path = '#'

            # add pagination if any
            pagination = render_pagination(base_path, pagination_page, pagination_total_pages)

            output = render_template_from_string(
                """
                <div class="list-pages-box w-list-pages"
                     data-list-pages-path-params="{{data_path_params}}"
                     data-list-pages-params="{{data_params}}"
                     data-list-pages-content="{{data_content}}"
                     data-list-pages-page-id="{{data_page_id}}">
                {{content}}
                {{pagination}}
                </div>
                """,
                content=output,
                pagination=pagination,
                data_path_params=json.dumps(context.path_params),
                data_params=json.dumps(params),
                data_content=json.dumps(content),
                data_page_id=articles.get_full_name(context.article) or ''
            )

        return output
