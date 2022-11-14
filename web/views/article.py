from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
import urllib.parse

from renderer.templates import apply_template
from renderer.utils import render_user_to_json
from web.models.articles import Article
from web.controllers import articles, permissions

from renderer import single_pass_render, single_pass_render_with_excerpt
from renderer.parser import RenderContext

from typing import Optional
import json

from web.models.sites import get_current_site

import re


class ArticleView(TemplateResponseMixin, ContextMixin, View):
    template_name = "page.html"
    template_404 = "page_404.html"
    template_403 = "page_403.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_path_params(path: str) -> tuple[str, dict[str, str]]:
        path = [urllib.parse.unquote(x) for x in path.split('/')]
        article_name = path[0]
        if not article_name:
            article_name = 'main'

        path_params = {}
        path = path[1:]
        i = 0
        while i < len(path):
            key = path[i]
            value = path[i + 1] if i + 1 < len(path) else None
            if key or value:
                path_params[key.lower()] = value
            i += 2

        return article_name, path_params

    def _render_nav(self, name: str, article: Article, path_params: dict[str, str]) -> str:
        nav = articles.get_article(name)
        if nav:
            return single_pass_render(articles.get_latest_source(nav), RenderContext(article, nav, path_params, self.request.user))
        return ""

    @staticmethod
    def get_page_path_params(path_params: dict[str, str], param: str):
        if param.startswith('path|'):
            k = param[5:].lower()
            if k in path_params:
                return path_params[k]
        elif param.startswith('path_expr|'):
            k = param[10:].lower()
            if k in path_params:
                return json.dumps(path_params[k])
        elif param.startswith('path_url|'):
            k = param[9:].lower()
            if k in path_params:
                return urllib.parse.quote(path_params[k], safe='')
        return '%%' + param + '%%'

    def render(self, fullname: str, article: Optional[Article], path_params: dict[str, str]) -> tuple[str, int, Optional[str], str, Optional[str], str]:
        excerpt = ''
        image = None
        if article is not None:
            if not permissions.check(self.request.user, 'view', article):
                context = {'page_id': fullname}
                content = render_to_string(self.template_403, context)
                redirect_to = None
                title = ''
                status = 403
            else:
                source = articles.get_latest_source(article)
                source = apply_template(source, lambda param: self.get_page_path_params(path_params, param))

                if article.name != '_template':
                    template = articles.get_article('%s:_template' % article.category)
                    if template:
                        template_source = articles.get_latest_source(template)
                        source = apply_template(template_source, {'content': source})
                context = RenderContext(article, article, path_params, self.request.user)
                content, excerpt, image = single_pass_render_with_excerpt(source, context)
                redirect_to = context.redirect_to
                title = context.title
                status = context.status
        else:
            name, category = articles.get_name(fullname)
            options = {'page_id': fullname, 'pathParams': path_params}
            context = {'options': json.dumps(options), 'allow_create': articles.is_full_name_allowed(fullname) and permissions.check(self.request.user, "create", Article(name=name, category=category))}
            content = render_to_string(self.template_404, context)
            redirect_to = None
            title = ''
            status = 404
        return content, status, redirect_to, excerpt, image, title

    def get_context_data(self, **kwargs):
        path = kwargs["path"]

        # wikidot hack: rewrite forum URLs to forum:start, forum:category, forum:thread
        # why do they need to support templates here?

        match re.match(r'^forum/start(.*)$', path):
            case re.Match() as match:
                path = 'forum:start' + match[1]

        match re.match(r'^forum/c-(\d+)(.*)$', path):
            case re.Match() as match:
                path = 'forum:category/c/' + match[1] + match[2]

        match re.match(r'^forum/t-(\d+)(.*)$', path):
            case re.Match() as match:
                path = 'forum:thread/t/' + match[1] + match[2]

        article_name, path_params = self.get_path_params(path)

        encoded_params = ''
        for param in path_params:
            encoded_params += '/%s' % param
            if path_params[param] is not None:
                encoded_params += '/%s' % urllib.parse.quote(path_params[param], safe='')

        normalized_article_name = articles.normalize_article_name(article_name)
        if normalized_article_name != article_name:
            return {'redirect_to': '/%s%s' % (normalized_article_name, encoded_params)}

        article = articles.get_article(article_name)
        breadcrumbs = [{'url': '/' + articles.get_full_name(x), 'title': x.title} for x in
                       articles.get_breadcrumbs(article)]

        # this is needed for parser debug logging so that page content is always the last printed
        nav_top = self._render_nav("nav:top", article, path_params)
        nav_side = self._render_nav("nav:side", article, path_params)

        content, status, redirect_to, excerpt, image, title = self.render(article_name, article, path_params)

        context = super(ArticleView, self).get_context_data(**kwargs)

        login_status_config = {
            'user': render_user_to_json(self.request.user)
        }

        site = get_current_site()
        article_rating, article_votes, article_rating_mode = articles.get_rating(article)

        comment_thread_id, comment_count = articles.get_comment_info(article)

        canonical_url = '//%s/%s%s' % (site.domain, article.full_name if article else article_name, encoded_params)

        options_config = {
            'optionsEnabled': status == 200,
            'editable': permissions.check(self.request.user, "edit", article),
            'lockable': permissions.check(self.request.user, "lock", article),
            'pageId': article_name,
            'rating': article_rating,
            'ratingMode': article_rating_mode,
            'ratingVotes': article_votes,
            'pathParams': path_params,
            'canRate': permissions.check(self.request.user, "rate", article),
            'canComment': permissions.check(self.request.user, "view-comments", article) if article else False,
            'commentThread': '/forum/t-%d/%s' % (comment_thread_id, articles.normalize_article_name(article.display_name)) if article else None,
            'commentCount': comment_count,
            'canDelete': permissions.check(self.request.user, "delete", article),
        }

        tags = []
        for tag_name in articles.get_tags(article):
            if tag_name.startswith('_'):
                continue
            tags.append({'link': '/system:page-tags/tag/%s#pages' % urllib.parse.quote(tag_name, safe=''), 'name': tag_name})

        print(repr(tags))

        context.update({
            'site_name': site.title,
            'site_headline': site.headline,
            'site_title': title or site.title,
            'site_icon': site.icon,

            'og_title': title or site.title,
            'og_description': excerpt,
            'og_image': image,
            'og_url': canonical_url,

            'nav_top': nav_top,
            'nav_side': nav_side,

            'title': title,
            'content': content,
            'tags': tags,
            'breadcrumbs': breadcrumbs,

            'login_status_config': json.dumps(login_status_config),
            'options_config': json.dumps(options_config),

            'status': status,
            'redirect_to': redirect_to,
        })

        return context

    def get(self, request, *args, **kwargs):
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        if context['redirect_to']:
            return HttpResponseRedirect(context['redirect_to'])
        return self.render_to_response(context, status=context['status'])
