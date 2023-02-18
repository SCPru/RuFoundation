import calendar
from datetime import datetime, timezone

from django.utils.safestring import SafeString

import renderer
from renderer.templates import apply_template
from renderer.utils import render_user_to_text, render_template_from_string
from renderer.parser import RenderContext
from system.models import User
from web.controllers import articles
from web.models.articles import Article, Vote, ArticleLogEntry, Tag
from web.models.settings import Settings
from django.db.models import Q, Value as V, F, Count, Sum, Avg, CharField, IntegerField, FloatField
from django.db.models.functions import Concat, Random, Coalesce
from web import threadvars
import json
import urllib.parse
import math
import re

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


def page_to_listpages_vars(page: Article, template, index, total):
    updated_by = None

    def get_updated_by():
        nonlocal updated_by
        if not updated_by:
            updated_by = articles.get_latest_log_entry(page).user

        return updated_by

    page_vars = LazyDict({
        'name': lambda: page.name,
        'category': lambda: page.category,
        'fullname': lambda: articles.get_full_name(page),
        'title': lambda: page.title,
        'title_linked': lambda: '[[[%s|]]]' % (articles.get_full_name(page)),
        'link': lambda: '/%s' % page.title,  # temporary, must be full page URL based on hostname
        'content': lambda: '[[include %s]]' % (articles.get_full_name(page)),
        'rating': lambda: articles.get_formatted_rating(page),
        'rating_votes': lambda: str(len(Vote.objects.filter(article=page))),
        'revisions': lambda: str(len(ArticleLogEntry.objects.filter(article=page))),
        'index': lambda: str(index),
        'total': lambda: str(total),
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
    if page.parent:
        page_vars['parent_name'] = lambda: page.parent.name
        page_vars['parent_category'] = lambda: page.parent.category
        page_vars['parent_fullname'] = lambda: articles.get_full_name(page.parent)
        page_vars['parent_title'] = lambda: page.parent.title
        page_vars['parent_title_linked'] = lambda: '[[[%s|%s]]]' % (articles.get_full_name(page.parent), page.parent.title)
    template = apply_template(template, lambda name: render_var(name, page_vars, page))
    return template


def split_arg_operator(arg, allowed, default):
    for op in allowed:
        if arg.startswith(op):
            return op, arg[len(op):]
    return default, arg


def query_pages(article, params, viewer=None, path_params=None, allow_pagination=True):
    if path_params is None:
        path_params = {}

    # legacy param aliases
    if 'created_at' not in params and 'date' in params:
        params['created_at'] = params['date']

    pagination_page = 1
    page_index = 0
    total_pages = 0

    # if either name, range, or fullname is '.', then we always select the current page.
    if params.get('name') == '.' or params.get('range') == '.' or params.get('fullname') == '.':
        pages = []
        if article:
            pages.append(article)
        pagination_total_pages = 1
        total_pages = 1
    elif params.get('fullname'):
        article = articles.get_article(params.get('fullname'))
        pages = []
        pagination_total_pages = 0
        if article:
            pages.append(article)
            pagination_total_pages += 1
            total_pages = 1
    else:
        # test
        q = Article.objects.prefetch_related("votes", "tags", "parent")

        f_type = params.get('pagetype', 'normal')
        if f_type != '*':
            if f_type == 'normal':
                q = q.filter(~Q(name__startswith='_'))
            elif f_type == 'hidden':
                q = q.filter(Q(name__startswith='_'))
        f_name = params.get('name', '*')
        if f_name != '*':
            f_name = f_name.replace('%', '*').lower()
            if f_name == '=':
                q = q.filter(name=article.name)
            elif '*' in f_name:
                up_to = f_name.index('*')
                q = q.filter(name__startswith=f_name[:up_to])
            else:
                q = q.filter(name=f_name)
        f_tags = params.get('tags', '*')
        if f_tags != '*':
            f_tags = f_tags.replace(',', ' ').lower()
            if f_tags == '-':
                q = q.filter(tags__isnull=True)
            elif f_tags == '=':
                tags = articles.get_tags(article)
                q = q.filter(tags__name__in=tags)
            elif f_tags == '==':
                tags = articles.get_tags(article)
                q = q.filter(tags__name__in=tags).annotate(num_tags=Count('tags')).filter(num_tags=len(tags))
            else:
                f_tags = [x.strip() for x in f_tags.split(' ') if x.strip()]
                one_allowed_tags = []
                for tag in f_tags:
                    if tag[0] == '-':
                        category, name = articles.get_name(tag[1:])
                        if category == "_default":
                            q = q.exclude(tags__name=name)
                        else:
                            q = q.exclude(tags__name=name, tags__category__slug=category)
                    elif tag[0] == '+':
                        category, name = articles.get_name(tag[1:])
                        if category == "_default":
                            q = q.filter(tags__name=name)
                        else:
                            q = q.filter(tags__name=name, tags__category__slug=category)
                    else:
                        one_allowed_tags.append(articles.get_tag(tag))
                if one_allowed_tags:
                    q = q.filter(tags__in=one_allowed_tags)
        f_category = params.get('category', '.')
        if f_category != '*':
            f_category = f_category.replace(',', ' ').lower()
            if f_category == '.':
                if article:
                    q = q.filter(category=article.category)
            else:
                categories = []
                not_allowed = []
                for category in f_category.split(' '):
                    if not category:
                        continue
                    if category == '.':
                        category = article.category
                    if category[0] == '-':
                        not_allowed.append(category[1:])
                    else:
                        categories.append(category)
                if categories:
                    q = q.filter(category__in=categories)
                if not_allowed:
                    q = q.filter(~Q(category__in=not_allowed))
        f_parent = params.get('parent')
        if f_parent:
            if f_parent == '-':
                q = q.filter(parent=None)
            elif f_parent == '=':
                q = q.filter(parent=article.parent)
            elif f_parent == '-=':
                q = q.filter(~Q(parent=article.parent))
            elif f_parent == '.':
                q = q.filter(parent=article)
            else:
                article = articles.get_article(f_parent)
                q = q.filter(parent=article)
        f_created_by = params.get('created_by')
        if f_created_by:
            if f_created_by == '.':
                user = viewer
            else:
                f_created_by = f_created_by.strip()
                if f_created_by.startswith('wd:'):
                    user = User.objects.filter(type=User.UserType.Wikidot, wikidot_username__iexact=f_created_by[3:])
                else:
                    user = User.objects.filter(username__iexact=f_created_by.strip())
                user = user[0] if user else None
            if not user or not user.is_authenticated:
                q = q.filter(id=-1)  # invalid
            else:
                q = q.filter(author=user)
        f_created_at = params.get('created_at')
        if f_created_at:
            if f_created_at.strip() == '=':
                if article:
                    day_start = article.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
                    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=0)
                    q = q.filter(created_at__gte=day_start, created_at__lte=day_end)
                else:
                    q = q.filter(id=-1)  # invalid
            else:
                op, f_created_at = split_arg_operator(f_created_at, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_created_at = f_created_at.strip()
                try:
                    dd = f_created_at.split('-')
                    year = int(dd[0])
                    first_date = datetime(year=year, month=1, day=1, tzinfo=timezone.utc)
                    last_date = datetime(year=year, month=12, day=31, tzinfo=timezone.utc)
                    if len(dd) >= 2:
                        month = int(dd[1])
                        month = max(1, min(12, month))
                        first_date = first_date.replace(month=month)
                        max_days = calendar.monthrange(year, month)[1]
                        last_date = last_date.replace(month=month, day=max_days)
                    else:
                        month = None  # this is just to silence pycharm
                    if len(dd) >= 3:
                        day = int(dd[2])
                        max_days = calendar.monthrange(year, month)[1]
                        day = max(1, min(max_days, day))
                        first_date = first_date.replace(day=day)
                        last_date = last_date.replace(day=day)
                    if op == '=':
                        q = q.filter(created_at__gte=first_date, created_at__lte=last_date)
                    elif op == '<>':
                        q = q.filter(Q(created_at__lt=first_date) | Q(created_at__gt=last_date))
                    elif op == '<':
                        q = q.filter(created_at__lt=first_date)
                    elif op == '>':
                        q = q.filter(created_at__gt=last_date)
                    elif op == '<=':
                        q = q.filter(created_at__lte=last_date)
                    elif op == '>=':
                        q = q.filter(created_at__gte=first_date)
                    else:
                        raise ValueError(op)
                except:
                    q = q.filter(id=-1)  # invalid

        # annotate each article with rating
        rating_func = F('id')
        if q:
            first_obj = q[0]
            obj_settings = first_obj.get_settings()
            if obj_settings.rating_mode == Settings.RatingMode.UpDown:
                rating_func = Coalesce(Sum('votes__rate'), 0)
            elif obj_settings.rating_mode == Settings.RatingMode.Stars:
                rating_func = Coalesce(Avg('votes__rate'), 0.0)
        q = q.annotate(rating=rating_func, num_votes=Count('votes'))
        # end annotate

        f_rating = params.get('rating')
        if f_rating:
            if f_rating.strip() == '=':
                if article is None:
                    q = q.filter(id=-1)
                else:
                    current_rating, votes, mode = articles.get_rating(article)
                    q = q.filter(rating=current_rating)
            else:
                op, f_rating = split_arg_operator(f_rating, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_rating = f_rating.strip()
                try:
                    try:
                        i_rating = int(f_rating)
                    except ValueError:
                        i_rating = float(f_rating)
                    if op == '=':
                        q = q.filter(rating=i_rating)
                    elif op == '<>':
                        q = q.filter(~Q(rating=i_rating))
                    elif op == '<':
                        q = q.filter(rating__lt=i_rating)
                    elif op == '>':
                        q = q.filter(rating__gt=i_rating)
                    elif op == '<=':
                        q = q.filter(rating__lte=i_rating)
                    elif op == '>=':
                        q = q.filter(rating__gte=i_rating)
                    else:
                        raise ValueError(op)
                except:
                    q = q.filter(id=-1)

        f_votes = params.get('votes')
        if f_votes:
            if f_votes.strip() == '=':
                if article is None:
                    q = q.filter(id=-1)
                else:
                    current_rating, votes, mode = articles.get_rating(article)
                    q = q.filter(num_votes=votes)
            else:
                op, f_votes = split_arg_operator(f_votes, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_votes = f_votes.strip()
                try:
                    try:
                        i_votes = int(f_votes)
                    except ValueError:
                        i_votes = float(f_votes)
                    if op == '=':
                        q = q.filter(num_votes=i_votes)
                    elif op == '<>':
                        q = q.filter(~Q(num_votes=i_votes))
                    elif op == '<':
                        q = q.filter(num_votes__lt=i_votes)
                    elif op == '>':
                        q = q.filter(num_votes__gt=i_votes)
                    elif op == '<=':
                        q = q.filter(num_votes__lte=i_votes)
                    elif op == '>=':
                        q = q.filter(num_votes__gte=i_votes)
                    else:
                        raise ValueError(op)
                except:
                    q = q.filter(id=-1)
        # sorting
        f_sort = params.get('order', 'created_at desc').split(' ')
        allowed_sort_columns = {
            'created_at': F('created_at'),
            'created_by': F('author'),
            'name': F('name'),
            'title': F('title'),
            'updated_at': F('updated_at'),
            'fullname': Concat('category', V(':'), 'name', output_field=CharField()),
            'rating': F('rating'),
            'votes': F('num_votes'),
            'random': Random(),
        }
        if f_sort[0] not in allowed_sort_columns:
            f_sort = ['created_at', 'desc']
        direction = 'desc' if f_sort[1:] == ['desc'] else 'asc'
        q = q.order_by(getattr(allowed_sort_columns[f_sort[0]], direction)())  # asc/desc is a function call on DB val
        q = q.distinct()
        # end sorting
        try:
            f_offset = int(params.get('offset', '0'))
        except:
            f_offset = 0
        page_index += f_offset
        try:
            f_limit = int(params.get('limit'))
            q = q[f_offset:f_offset + f_limit]
        except:
            q = q[f_offset:]
        total_pages = q.count()
        if allow_pagination:
            try:
                f_per_page = int(params.get('perpage', '20'))
            except:
                f_per_page = 20
            try:
                f_page = int(path_params.get('p', '1'))
                if f_page < 1:
                    f_page = 1
            except:
                f_page = 1
            if f_page != 1:
                page_index += (f_page - 1) * f_per_page
            q = q[(f_page - 1) * f_per_page:f_page * f_per_page]
            pagination_page = f_page
            pagination_total_pages = int(math.ceil(total_pages / f_per_page))
        else:
            pagination_page = 1
            pagination_total_pages = 1
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
            if v.startswith('@URL|'):
                default = v[5:]
                if k in context.path_params:
                    params[k] = context.path_params[k]
                else:
                    params[k] = default

        prepend = params.get('prependline', '')
        append = params.get('appendline', '')
        separate = params.get('separate', 'yes') == 'yes'
        wrapper = params.get('wrapper', 'yes') == 'yes'

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
        if params.get('reverse', 'no') == 'yes':
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
