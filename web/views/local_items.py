from django.http import HttpResponseNotFound, HttpResponseForbidden, HttpResponse, HttpRequest
from django.views.generic.base import View

from renderer import RenderContext, single_pass_fetch_code_and_html, single_pass_render
from renderer.html import get_html_injected_code
from web.controllers import articles

import json
import hashlib


class LocalCodeView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request: HttpRequest, page_id: str, index: int, *args, **kwargs):
        article = articles.get_article(page_id)
        if not article:
            return HttpResponseNotFound('Article not found')

        if not request.user.has_perm('roles.view_articles', article):
            return HttpResponseForbidden('Permission denied')

        rev_num = request.GET.get('revNum')
        if rev_num is not None:
            source = articles.get_source_at_rev_num(article, int(rev_num)) or ''
        else:
            source = articles.get_latest_source(article) or ''

        context = RenderContext(article, article, json.loads(request.GET.get('pathParams', "{}")), self.request.user)
        code, _ = single_pass_fetch_code_and_html(source, context, includes=False)

        index -= 1

        if index < 0 or index >= len(code):
            return HttpResponseNotFound('Code block not found')

        mime_type = 'text/plain'
        language = code[index][0].lower()
        if language in ('html', 'xhtml'):
            mime_type = 'text/html'
        elif language in ('javascript', 'js', 'jsx'):
            mime_type = 'text/javascript'
        elif language == 'xml':
            mime_type = 'application/xml'
        elif language == 'css':
            mime_type = 'text/css'

        response = HttpResponse(content_type=f'{mime_type}; charset=utf-8')
        content = code[index][1].encode('utf-8')

        response['Content-Length'] = len(content)
        response.content = content
        response.status_code = 200

        return response


class LocalHTMLView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request: HttpRequest, page_id: str, hash_and_id: str, *args, **kwargs):
        response = HttpResponse(content_type='text/html; charset=utf-8')

        article = articles.get_article(page_id)
        if not article:
            return HttpResponseNotFound('Article not found')

        if not request.user.has_perm('roles.view_articles', article):
            return HttpResponseForbidden('Permission denied')

        rev_num = request.GET.get('revNum')
        if rev_num is not None:
            source = articles.get_source_at_rev_num(article, int(rev_num)) or ''
        else:
            source = articles.get_latest_source(article) or ''

        context = RenderContext(article, article, json.loads(request.GET.get('pathParams', "{}")), self.request.user)
        _, html = single_pass_fetch_code_and_html(source, context, includes=True)

        html_by_hash = dict()

        for s in html:
            h = hashlib.md5(s.encode('utf-8')).hexdigest()
            html_by_hash[h] = s

        requested_hash, requested_id = hash_and_id.split('-', 1)

        if requested_hash not in html_by_hash:
            return HttpResponseNotFound('HTML block not found')

        prepend_code = get_html_injected_code(requested_id)

        content = (prepend_code + html_by_hash[requested_hash]).encode('utf-8')

        response['Content-Length'] = len(content)
        response.content = content
        response.status_code = 200

        return response


class LocalThemeView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, request: HttpRequest, page_id: str, *args, **kwargs):
        article = articles.get_article(page_id)
        if not article:
            return HttpResponseNotFound('Article not found')

        if not request.user.has_perm('roles.view_articles', article):
            return HttpResponseForbidden('Permission denied')

        rev_num = request.GET.get('revNum')
        if rev_num is not None:
            source = articles.get_source_at_rev_num(article, int(rev_num)) or ''
        else:
            source = articles.get_latest_source(article) or ''

        # delete blocks between noinclude
        noinclude_start = '[[noinclude]]'
        noinclude_end = '[[/noinclude]]'
        while True:
            next_noinclude = source.find(noinclude_start)
            if next_noinclude < 0:
                break
            closing_noinclude = source.find(noinclude_end, next_noinclude)
            source = source[:next_noinclude] + source[closing_noinclude+len(noinclude_end):]

        include_params = json.loads(request.GET.get('includeParams', "{}"))
        for k in include_params:
            source = source.replace('{$%s}' % k, include_params[k])

        context = RenderContext(article, article, json.loads(request.GET.get('pathParams', "{}")), self.request.user)
        single_pass_render(source, context)

        response = HttpResponse(content_type='text/css; charset=utf-8')
        content = context.add_css.encode('utf-8')

        response['Content-Length'] = len(content)
        response.content = content
        response.status_code = 200

        return response
