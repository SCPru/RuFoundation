import renderer
from renderer.parser import RenderContext
from web.controllers import articles
import re
from web.models.articles import Article
from django.db.models import Q, Value as V
from django.db.models.functions import Concat


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
        'content': articles.get_latest_source(page),
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


def render(context, params, content=None):
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

    # if either name, range, or fullname is '.', then we always select the current page.
    if params.get('name') == '.' or params.get('range') == '.' or params.get('fullname') == '.':
        pages = []
        if context.article:
            pages.append(context.article)
        total_pages = 1
    elif params.get('fullname'):
        article = articles.get_article(params.get('fullname'))
        pages = []
        total_pages = 0
        if article:
            pages.append(article)
            total_pages += 1
    else:
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
        f_sort = params.get('order', 'created_at desc').split(' ')
        # sorting
        allowed_sort_columns = {
            'created_at': V('created_at'),
            'name': V('name'),
            'title': V('title'),
            'updated_at': V('updated_at'),
            'fullname': Concat('category', V(':'), 'name')
        }
        if f_sort[0] not in allowed_sort_columns:
            f_sort = ['created_at', 'desc']
        direction = 'asc' if f_sort[1:] == ['desc', 'desc'] else 'desc'
        q = q.order_by(getattr(allowed_sort_columns[f_sort[0]], direction)())  # asc/desc is a function call on DB val
        # end sorting
        total_pages = len(q)
        try:
            f_offset = int(params.get('offset', '0'))
        except:
            f_offset = 0
        q = q[f_offset:]
        f_limit = params.get('limit')
        if f_limit:
            try:
                f_limit = int(f_limit)
                q = q[:f_limit]
            except:
                pass
        try:
            f_per_page = int(params.get('perPage', '20'))
        except:
            f_per_page = 20
        try:
            f_page = int(params.get('page', '1'))
        except:
            f_page = 1
        q = q[(f_page-1)*f_per_page:f_page*f_per_page]
        pages = list(q)
        if params.get('reverse', 'no') == 'yes':
            pages = reversed(pages)

    output = ''
    common_context = RenderContext(context.article, context.article, context.path_params)

    if separate:
        if prepend:
            output += renderer.single_pass_render(prepend+'\n', common_context)
        for page in pages:
            page_content = page_to_listpages_vars(page, content)
            output += renderer.single_pass_render(page_content+'\n', RenderContext(page, page, context.path_params))
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
        output = '<div class="list-pages-box">' + output + '</div>'

    return output