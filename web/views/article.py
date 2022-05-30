from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.conf import settings

from web.models.articles import Article
from web.controllers import articles

from renderer import single_pass_render
from renderer.parser import RenderContext

from typing import Optional
import json


class ArticleView(TemplateResponseMixin, ContextMixin, View):
    template_name = "page.html"
    template_404 = "page_404.html"

    @staticmethod
    def get_path_params(path: str) -> tuple[str, dict[str, str]]:
        path = path.split('/')
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

    @staticmethod
    def _render_nav(name: str, article: Article, path_params: dict[str, str]) -> str:
        nav = articles.get_article(name)
        if nav:
            return single_pass_render(articles.get_latest_source(nav), RenderContext(article, nav, path_params))
        return ""

    def render(self, fullname: str, article: Optional[Article], path_params: dict[str, str]) -> tuple[str, int, Optional[str]]:
        if article is not None:
            context = RenderContext(article, article, path_params)
            content = single_pass_render(articles.get_latest_source(article), context)
            redirect_to = context.redirect_to
            status = 200
        else:
            context = {'page_id': fullname, 'allow_create': articles.is_full_name_allowed(
                fullname) and settings.ANONYMOUS_EDITING_ENABLED}
            content = render_to_string(self.template_404, context)
            redirect_to = None
            status = 404
        return content, status, redirect_to

    def get_context_data(self, **kwargs):
        path = kwargs["path"]

        article_name, path_params = self.get_path_params(path)

        article = articles.get_article(article_name)
        title = article.title if article and article_name != 'main' else None
        breadcrumbs = [{'url': '/' + articles.get_full_name(x), 'title': x.title} for x in
                       articles.get_breadcrumbs(article)]

        content, status, redirect_to = self.render(article_name, article, path_params)

        context = super(ArticleView, self).get_context_data(**kwargs)

        options_config = {
            'optionsEnabled': True,
            'editable': settings.ANONYMOUS_EDITING_ENABLED,
            'pageId': article_name
        }

        context.update({
            'site_name': settings.WEBSITE_NAME,
            'site_headline': settings.WEBSITE_HEADLINE,
            'site_title': title or settings.WEBSITE_NAME,
            'content': content,
            'nav_top': self._render_nav("nav:top", article, path_params),
            'nav_side': self._render_nav("nav:side", article, path_params),
            'breadcrumbs': breadcrumbs,
            'title': title,
            'status': status,
            'options_config': json.dumps(options_config),
            'redirect_to': redirect_to
        })

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['redirect_to']:
            return HttpResponseRedirect(context['redirect_to'])
        return self.render_to_response(context, status=context['status'])
