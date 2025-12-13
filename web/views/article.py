import re
import json
import datetime
import urllib.parse

from typing import Optional, Tuple

from django.conf import settings
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect

from web.models.site import get_current_site
from web.models.articles import Article, Category
from web.models.notifications import UserNotificationMapping
from web.controllers import articles, notifications
from web.util.css import normalize_computed_style

from modules.listpages import page_to_listpages_vars

from renderer.templates import apply_template
from renderer.utils import render_user_to_json
from renderer import single_pass_render, single_pass_render_with_excerpt
from renderer.parser import RenderContext


class ArticleView(TemplateResponseMixin, ContextMixin, View):
    template_name = "page.html"
    template_404 = "page_404.html"
    template_403 = "page_403.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_path_params(path: str) -> tuple[str, dict[str, str]]:
        path = [urllib.parse.unquote(x) for x in path.split('/')]
        article_name = path[0].strip()
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
            context = RenderContext(article, nav, path_params, self.request.user)
            return single_pass_render(articles.get_latest_source(nav), context), context.computed_style
        return '', ''

    @staticmethod
    def get_this_page_params(path_params: dict[str, str], param: str, more_params: Optional[dict[str, str]]=None):
        if param.startswith('path|'):
            k = param[5:].lower()
            if k in path_params:
                return path_params[k]
        elif param.startswith('path_expr|'):
            k = param[10:].lower()
            if k in path_params:
                return json.dumps(path_params[k])
            return json.dumps('%%' + param + '%%')
        elif param.startswith('path_url|'):
            k = param[9:].lower()
            if k in path_params:
                return urllib.parse.quote(path_params[k], safe='')
            return urllib.parse.quote('%%' + param + '%%', safe='')
        elif more_params is not None and param in more_params:
            return more_params[param]
        return '%%' + param + '%%'

    def render(self, fullname: str, article: Optional[Article], path_params: dict[str, str], canonical_url: str) -> Tuple[str, int, Optional[str], str, Optional[str], str, int, Optional[datetime.datetime]]:
        excerpt = ''
        image = None
        rev_number = 0
        updated_at = None
        computed_style = ''
        if article is not None:
            template_source = '%%content%%'

            if article.name != '_template':
                template = articles.get_article('%s:_template' % article.category)
                if template:
                    template_source = articles.get_latest_source(template)

            source = page_to_listpages_vars(article, template_source, index=1, total=1)
            source = apply_template(source, lambda param: self.get_this_page_params(path_params, param, {'canonical_url': canonical_url}))
            context = RenderContext(article, article, path_params, self.request.user)
            content, excerpt, image = single_pass_render_with_excerpt(source, context)
            redirect_to = context.redirect_to
            title = context.title
            status = context.status
            computed_style = context.computed_style

            rev_number = articles.get_latest_log_entry(article).rev_number
            updated_at = article.updated_at
            if context.og_image:
                image = context.og_image
            if context.og_description:
                excerpt = context.og_description
        else:
            category, _ = articles.get_name(fullname)
            options = {'page_id': fullname, 'pathParams': path_params}
            context = {'options': json.dumps(options), 'allow_create': articles.is_full_name_allowed(fullname) and self.request.user.has_perm('roles.create_articles', Category.get_or_default_category(category))}
            content = render_to_string(self.template_404, context)
            redirect_to = None
            title = ''
            status = 404
        return content, status, redirect_to, excerpt, image, title, rev_number, updated_at, computed_style

    def get_context_data(self, **kwargs):
        path = kwargs["path"]
        status = None
        content = None

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

        match re.match(r'^forum/s-(\d+)(.*)$', path):
            case re.Match() as match:
                path = 'forum:start/s/' + match[1] + match[2]

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
        perms_obj = article or articles.get_article_category(article_name)
        if perms_obj and not self.request.user.has_perm('roles.view_articles', perms_obj):
            content = render_to_string(self.template_403, {'page_id': article_name})
            status = 403
            article = None
        
        comment_thread_id, comment_count = articles.get_comment_info(article)
        breadcrumbs = [{'url': '/' + articles.get_full_name(x), 'title': x.title} for x in
                       articles.get_breadcrumbs(article)]

        if article is not None and path_params.get('comments') == 'show':
            return {'redirect_to': '/forum/t-%d/%s' % (comment_thread_id, articles.normalize_article_name(article.display_name))}

        # this is needed for parser debug logging so that page content is always the last printed
        nav_top, nav_top_styles = self._render_nav("nav:top", article, path_params)
        nav_side, nav_side_styles = self._render_nav("nav:side", article, path_params)

        site = get_current_site()
        canonical_url = '//%s/%s%s' % (site.domain, article.full_name if article else article_name, encoded_params)

        rendered_content, rendered_status, redirect_to, excerpt, image, title, rev_number, updated_at, computed_style = self.render(article_name, article, path_params, canonical_url)

        context = super(ArticleView, self).get_context_data(**kwargs)

        notification_count = UserNotificationMapping.objects.filter(recipient=self.request.user, is_viewed=False).count() if self.request.user.is_authenticated else 0

        login_status_config = {
            'user': render_user_to_json(self.request.user),
            'notificationCount': notification_count
        }

        article_rating, article_votes, article_popularity, article_rating_mode = articles.get_rating(article)

        options_config = {
            'optionsEnabled': article is not None,
            'editable': self.request.user.has_perm('roles.edit_articles', article),
            'lockable': self.request.user.has_perm('roles.lock_articles', article),
            'tagable': self.request.user.has_perm('roles.tag_articles', article),
            'pageId': article_name,
            'rating': article_rating,
            'ratingMode': article_rating_mode,
            'ratingVotes': article_votes,
            'ratingPopularity': article_popularity,
            'pathParams': path_params,
            'canRate': self.request.user.has_perm('roles.rate_articles', article),
            'canComment': self.request.user.has_perm('roles.comment_articles', article) if article else False,
            'canViewComments': self.request.user.has_perm('roles.view_article_comments', article) if article else False,
            'commentThread': ('/%s/comments/show' % normalized_article_name) if article else None,
            'commentCount': comment_count,
            'canDelete': self.request.user.has_perm('roles.delete_articles', article),
            'canCreateTags': site.settings.creating_tags_allowed,
            'canManageFiles': self.request.user.has_perm('roles.manage_article_files', article),
            'canRename': self.request.user.has_perm('roles.move_articles', article),
            'canCreateHere': self.request.user.has_perm('roles.create_articles', article),
            'canManageAuthors': self.request.user.has_perm('roles.manage_article_authors', article),
            'canResetVotes': self.request.user.has_perm('roles.reset_article_votes', article),
            'canWatch': not self.request.user.is_anonymous,
            'preferences': {} if self.request.user.is_anonymous else self.request.user.preferences.all(),
            'isWatching': not self.request.user.is_anonymous and (
                notifications.is_subscribed(self.request.user, article=article) or \
                notifications.is_subscribed(self.request.user, forum_thread=path_params.get("t"))
            ),
        }

        tags_categories = articles.get_tags_categories(article)

        computed_style = normalize_computed_style(nav_top_styles + nav_side_styles + computed_style)

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
            'content': content or rendered_content,
            'tags_categories': tags_categories,
            'breadcrumbs': breadcrumbs,
            'rev_number': rev_number,
            'updated_at': updated_at,

            'login_status_config': json.dumps(login_status_config),
            'options_config': json.dumps(options_config),

            'computed_style': computed_style,

            'status': status or rendered_status,
            'redirect_to': redirect_to
        })

        if settings.GOOGLE_TAG_ID:
            context.update({
                'google_tag_id': settings.GOOGLE_TAG_ID
            })

        category_name, _ = articles.get_name(article_name)
        category = Category.get_or_default_category(category_name)
        context.update({
            'noindex': not category.is_indexed
        })

        return context

    def get(self, request, *args, **kwargs):
        path = request.META['RAW_PATH'][1:]
        context = self.get_context_data(path=path)
        if context.get('redirect_to'):
            return HttpResponseRedirect(context['redirect_to'])
        return self.render_to_response(context, status=context['status'])
