from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect

from renderer.templates import apply_template
from renderer.utils import render_user_to_json
from web.models.articles import Article
from web.controllers import articles, permissions

from renderer import single_pass_render
from renderer.parser import RenderContext

from typing import Optional
import json

from web.models.sites import get_current_site


class ArticleView(TemplateResponseMixin, ContextMixin, View):
    template_name = "page.html"
    template_404 = "page_404.html"
    template_403 = "page_403.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def _render_nav(self, name: str, article: Article, path_params: dict[str, str]) -> str:
        nav = articles.get_article(name)
        if nav:
            return single_pass_render(articles.get_latest_source(nav), RenderContext(article, nav, path_params, self.request.user))
        return ""

    def render(self, fullname: str, article: Optional[Article], path_params: dict[str, str]) -> tuple[str, int, Optional[str]]:
        if article is not None:
            if not permissions.check(self.request.user, 'view', article):
                context = {'page_id': fullname}
                content = render_to_string(self.template_403, context)
                redirect_to = None
                status = 403
            else:
                source = articles.get_latest_source(article)
                if article.name != '_template':
                    template = articles.get_article('%s:_template' % article.category)
                    if template:
                        template_source = articles.get_latest_source(template)
                        source = apply_template(template_source, {'content': source})
                context = RenderContext(article, article, path_params, self.request.user)
                content = single_pass_render(source, context)
                redirect_to = context.redirect_to
                status = 200
        else:
            name, category = articles.get_name(fullname)
            context = {'page_id': fullname, 'allow_create': articles.is_full_name_allowed(fullname) and permissions.check(self.request.user, "create", Article(name=name, category=category))}
            content = render_to_string(self.template_404, context)
            redirect_to = None
            status = 404
        return content, status, redirect_to

    def get_context_data(self, **kwargs):
        path = kwargs["path"]

        article_name, path_params = self.get_path_params(path)

        article = articles.get_article(article_name)
        title = article.title.strip() if article and article_name != 'main' else None
        breadcrumbs = [{'url': '/' + articles.get_full_name(x), 'title': x.title} for x in
                       articles.get_breadcrumbs(article)]

        # this is needed for parser debug logging so that page content is always the last printed
        nav_top = self._render_nav("nav:top", article, path_params)
        nav_side = self._render_nav("nav:side", article, path_params)

        content, status, redirect_to = self.render(article_name, article, path_params)

        context = super(ArticleView, self).get_context_data(**kwargs)

        login_status_config = {
            'user': render_user_to_json(self.request.user)
        }

        site = get_current_site()
        article_rating, article_votes, article_rating_mode = articles.get_rating(article)

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
            'canDelete': permissions.check(self.request.user, "delete", article),
        }

        context.update({
            'site_name': site.title,
            'site_headline': site.headline,
            'site_title': title or site.title,
            'site_icon': site.icon,

            'nav_top': nav_top,
            'nav_side': nav_side,

            'title': title,
            'content': content,
            'tags': [x for x in articles.get_tags(article) if not x.startswith('_')],
            'breadcrumbs': breadcrumbs,

            'login_status_config': json.dumps(login_status_config),
            'options_config': json.dumps(options_config),

            'status': status,
            'redirect_to': redirect_to,
        })

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['redirect_to']:
            return HttpResponseRedirect(context['redirect_to'])
        return self.render_to_response(context, status=context['status'])
