import renderer
from renderer.parser import RenderContext
from web.controllers import articles
import re
from web.models.articles import Article
from django.db.models import Q, Value as V, F, Count
from django.db.models.functions import Concat
from web import threadvars
import json
from django.utils import html
import urllib.parse
import math


def has_content():
    return True


def render_date(date):
    if not date:
        return 'n/a'
    return date.strftime('%H:%M %d.%m.%Y')


def render_var(var, page_vars, page):
    var = var[2]
    if var in page_vars:
        return page_vars[var]
    if var.startswith('created_at|'):
        format = var[11:].strip()
        try:
            return page.created_at.strftime(format)
        except:
            return page_vars['created_at']
    if var.startswith('updated_at|'):
        format = var[11:].strip()
        try:
            return page.updated_at.strftime(format)
        except:
            return page_vars['updated_at']
    return '%%' + var + '%%'


def page_to_listpages_vars(page, template):
    page_vars = {
        'name': page.name,
        'category': page.category,
        'fullname': articles.get_full_name(page),
        'title': page.title,
        'title_linked': '[[[%s|%s]]]' % (articles.get_full_name(page), page.title),
        'link': '/%s' % page.title,  # temporary, must be full page URL based on hostname
        'content': '[[include %s]]' % (articles.get_full_name(page)),
        # content{n} = content sections are not supported yet
        # preview and preview(n) = first characters of the page are not supported yet
        # summary = wtf is this?
        # tags, tags_linked, tags_linked|link_prefix = not yet
        # _tags, _tags_linked, _tags_linked|link_prefix = not yet
        # form_data{name}, form_raw{name}, form_label{name}, form_hint{name} = never ever
        'created_at': render_date(page.created_at),
        'updated_at': render_date(page.updated_at),
        # created_by, created_by_unix, created_by_id, created_by_linked = not yet
        # updated_by, updated_by_unix, updated_by_id, updated_by_linked = not yet
        # commented_at, commented_by, commented_by_unix, commented_by_id, commented_by_linked = not yet
    }
    if page.parent:
        page_vars['parent_name'] = page.parent.name
        page_vars['parent_category'] = page.parent.category
        page_vars['parent_fullname'] = articles.get_full_name(page.parent)
        page_vars['parent_title'] = page.parent.title
        page_vars['parent_title_linked'] = '[[[%s|%s]]]' % (articles.get_full_name(page.parent), page.parent.title)
    template = re.sub(r'(%%(.*?)%%)', lambda var: render_var(var, page_vars, page), template)
    return template


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

        prepend = params.get('prependLine', '')
        append = params.get('appendLine', '')
        separate = params.get('separate', 'yes') == 'yes'
        wrapper = params.get('wrapper', 'yes') == 'yes'

        pagination_page = 1
        pagination_total_pages = 1

        # if either name, range, or fullname is '.', then we always select the current page.
        if params.get('name') == '.' or params.get('range') == '.' or params.get('fullname') == '.':
            pages = []
            if context.article:
                pages.append(context.article)
            pagination_total_pages = 1
        elif params.get('fullname'):
            article = articles.get_article(params.get('fullname'))
            pages = []
            pagination_total_pages = 0
            if article:
                pages.append(article)
                pagination_total_pages += 1
        else:
            # test
            q = Article.objects

            f_type = params.get('pagetype', 'normal')
            if f_type != '*':
                if f_type == 'normal':
                    q = q.filter(~Q(name__startswith='_'))
                elif f_type == 'hidden':
                    q = q.filter(Q(name__startswith='_'))
            f_name = params.get('name', '*')
            if f_name != '*':
                f_name = f_name.replace('%', '*')
                if f_name == '=':
                    q = q.filter(name=context.article.name)
                elif '*' in f_name:
                    up_to = f_name.index('*')
                    q = q.filter(name__startswith=f_name[:up_to])
                else:
                    q = q.filter(name=f_name)
            f_tags = params.get('tags', '*')
            if f_tags != '*':
                f_tags = f_tags.replace(',', ' ')
                if f_tags == '-':
                    q = q.filter(tags__isnull=True)
                elif f_tags == '=':
                    tags = articles.get_tags(context.article)
                    q = q.filter(tags__name__in=tags)
                elif f_tags == '==':
                    tags = articles.get_tags(context.article)
                    q = q.filter(tags__name__in=tags).annotate(num_tags=Count('tags')).filter(num_tags=len(tags))
                else:
                    f_tags = [x.strip() for x in f_tags.split(' ') if x.strip()]
                    required_tags = []
                    not_allowed_tags = []
                    required_one = []
                    for tag in f_tags:
                        if tag[0] == '-':
                            not_allowed_tags.append(tag[1:])
                        elif tag[0] == '+':
                            required_tags.append(tag[1:])
                        else:
                            required_one.append(tag)
                    if required_one:
                        q = q.filter(tags__name__in=required_one)
                    for tag in required_tags:
                        q = q.filter(tags__name__in=[tag])
                    if not_allowed_tags:
                        q = q.filter(~Q(tags__name__in=not_allowed_tags))
            f_category = params.get('category', '.')
            if f_category != '*':
                f_category = f_category.replace(',', ' ')
                if f_category == '.':
                    q = q.filter(category=context.article.category)
                else:
                    categories = []
                    not_allowed = []
                    for category in f_category.split(' '):
                        if not category:
                            continue
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
                    q = q.filter(parent=context.article.parent)
                elif f_parent == '-=':
                    q = q.filter(~Q(parent=context.article.parent))
                elif f_parent == '.':
                    q = q.filter(parent=context.article)
                else:
                    article = articles.get_article(f_parent)
                    q = q.filter(parent=article)
            # sorting
            f_sort = params.get('order', 'created_at desc').split(' ')
            allowed_sort_columns = {
                'created_at': F('created_at'),
                'name': F('name'),
                'title': F('title'),
                'updated_at': F('updated_at'),
                'fullname': Concat('category', V(':'), 'name')
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
            try:
                f_limit = int(params.get('limit'))
                q = q[f_offset:f_offset + f_limit]
            except:
                q = q[f_offset:]
            total_pages = len(q)
            try:
                f_per_page = int(params.get('perPage', '20'))
            except:
                f_per_page = 20
            try:
                f_page = int(context.path_params.get('p', '1'))
                if f_page < 1:
                    f_page = 1
            except:
                f_page = 1
            q = q[(f_page-1)*f_per_page:f_page*f_per_page]
            pages = list(q)
            if params.get('reverse', 'no') == 'yes':
                pages = reversed(pages)
            pagination_page = f_page
            pagination_total_pages = int(math.ceil(total_pages / f_per_page))

        output = ''
        common_context = RenderContext(context.article, context.article, context.path_params, context.user)

        if separate:
            if prepend:
                output += renderer.single_pass_render(prepend+'\n', common_context)
            for page in pages:
                page_content = page_to_listpages_vars(page, content)
                output += renderer.single_pass_render(page_content+'\n', RenderContext(page, page, context.path_params, context.user))
            if append:
                output += renderer.single_pass_render(append, common_context)
        else:
            source = ''
            if prepend:
                source += prepend+'\n'
            for page in pages:
                page_content = page_to_listpages_vars(page, content)
                source += page_content+'\n'
            source += append
            output += renderer.single_pass_render(source, common_context)

        if wrapper:
            list_pages_attrs = ''
            list_pages_attrs += 'data-list-pages-path-params="%s"' % html.escape(json.dumps(context.path_params))
            list_pages_attrs += ' data-list-pages-params="%s"' % html.escape(json.dumps(params))
            list_pages_attrs += ' data-list-pages-content="%s"' % html.escape(json.dumps(content))
            list_pages_attrs += ' data-list-pages-page-id="%s"' % html.escape(context.article.full_name)

            base_path = '/%s' % context.article.full_name
            for k, v in context.path_params.items():
                if k != 'p':
                    base_path += '/%s/%s' % (urllib.parse.quote_plus(str(k)), urllib.parse.quote_plus(str(v)))

            # add pagination if any
            if pagination_total_pages > 1:
                output += '<div class="pager">'
                output += '<span class="pager-no">страница&nbsp;%d&nbsp;из&nbsp;%d</span>' % (pagination_page, pagination_total_pages)
                if pagination_page > 1:
                    output += '<span class="target"><a href="%s/p/%d" data-pagination-target="%d">&laquo;&nbsp;предыдущая</a></span>' % (base_path, pagination_page+1, pagination_page+1)
                around_pages = 2
                left_from = 1
                left_to = left_from + 1
                if pagination_page < (around_pages*2+1):
                    left_to = around_pages+1
                right_to = pagination_total_pages
                right_from = max(left_to+1, right_to - 1)
                if pagination_page > (right_to - (around_pages*2+1)):
                    right_from = max(left_to+1, pagination_total_pages - (around_pages+1))
                center_from = max(left_to+1, pagination_page - around_pages)
                center_to = min(right_from-1, pagination_page + around_pages)
                for i in range(left_from, left_to+1):
                    if pagination_page == i:
                        output += '<span class="target current">%d</span>' % (i)
                    else:
                        output += '<span class="target"><a href="%s/p/%d" data-pagination-target="%d">%d</a></span>' % (base_path, i, i, i)
                if center_from > left_to+1:
                    output += '<span class="dots">...</span>'
                for i in range(center_from, center_to+1):
                    if pagination_page == i:
                        output += '<span class="target current">%d</span>' % (i)
                    else:
                        output += '<span class="target"><a href="%s/p/%d" data-pagination-target="%d">%d</a></span>' % (base_path, i, i, i)
                if center_to < right_from-1:
                    output += '<span class="dots">...</span>'
                for i in range(right_from, right_to+1):
                    if pagination_page == i:
                        output += '<span class="target current">%d</span>' % (i)
                    else:
                        output += '<span class="target"><a href="%s/p/%d" data-pagination-target="%d">%d</a></span>' % (base_path, i, i, i)
                if pagination_page < pagination_total_pages:
                    output += '<span class="target"><a href="%s/p/%d" data-pagination-target="%d">следующая&nbsp;&raquo;</a></span>' % (base_path, pagination_page+1, pagination_page+1)
                print('left: %s, center: %s, right: %s' % (repr((left_from, left_to)), repr((center_from, center_to)), repr((right_from, right_to))))
                output += '</div>'

            output = '<div class="list-pages-box w-list-pages" %s>%s</div>' % (list_pages_attrs, output)

        return output
