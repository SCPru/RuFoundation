import re
from typing import Optional

from django.db.models import TextField, Value
from django.db.models.functions import Concat, Lower
from django.utils.safestring import SafeString

import modules
from system.models import User
from web import threadvars
from web.models.articles import ArticleVersion, Article
from web.models.sites import get_current_site
from . import expression
from .parser import RenderContext
from .utils import render_user_to_html, render_template_from_string

import os


# FTML is not imported globally to prevent loading DLL for commands that don't require it


def callbacks_with_context(context):
    from ftml import ftml

    class CallbacksWithContextImpl(ftml.Callbacks):
        def __init__(self, context):
            super().__init__()
            self.context = context

        def module_has_body(self, module_name: str) -> bool:
            return modules.module_has_content(module_name.lower())

        def render_module(self, module_name: str, params: dict[str, str], body: str) -> str:
            params_for_module = {key.lower(): value for (key, value) in params.items()}
            try:
                return modules.render_module(module_name, self.context, params_for_module, content=body)
            except modules.ModuleError as e:
                return self.render_template('<div class="error-block"><p>{{error}}</p></div>', error=e.message)

        def render_user(self, user: str, avatar: bool) -> str:
            try:
                if user.lower().startswith('wd:'):
                    user = User.objects.get(type=User.UserType.Wikidot, wikidot_username=user[3:])
                else:
                    user = User.objects.get(username=user)
                return render_user_to_html(user, avatar=avatar)
            except User.DoesNotExist:
                return render_template_from_string(
                    '<span class="error-inline">Пользователь \'{{username}}\' не существует</span>',
                    username=user
                )

        def get_i18n_message(self, message_id: str) -> str:
            messages = {
                "button-copy-clipboard": "Скопировать",
                "collapsible-open": "+ открыть блок",
                "collapsible-hide": "- закрыть блок",
                "table-of-contents": "Содержание",
                "toc-open": "Раскрыть",
                "toc-close": "Свернуть",
                "footnote": "Сноска",
                "footnote-block-title": "Сноски",
                "image-context-bad": "Некорректный адрес изображения",
            }
            return messages.get(message_id, '?')

        def render_include_not_found(self, full_name: str) -> str:
            from web.controllers import articles

            include_name = articles.normalize_article_name(full_name)
            if include_name in threadvars.get('include_err', []):
                return '[[div class="error-block"]]Вставленная страница "%s" вызывает бесконечный цикл включений[[/div]]' % full_name
            else:
                # this must return Wiki markup because of the stage it runs at.
                return '[[div class="error-block"]]Вставленная страница "%s" не существует ([[a href="/%s/edit/true" target="_blank"]]создать её сейчас[[/a]])[[/div]]' % (full_name, full_name)

        # This function converts magical _default category to explicit _default category
        # This is so that we can later reuse this in the database query that will just concat the category+name for articles
        @staticmethod
        def _page_name_to_dumb(name):
            return ('_default:%s' % name).lower() if ':' not in name else name.lower()

        def fetch_includes(self, include_refs: list[ftml.IncludeRef]) -> list[ftml.FetchedPage]:
            from web.controllers import articles

            refs_as_dumb = [self._page_name_to_dumb(x.full_name) for x in include_refs]
            included = ArticleVersion.objects\
                .select_related('article')\
                .annotate(full_name=Lower(Concat('article__category', Value(':'), 'article__name', output_field=TextField())))\
                .filter(full_name__in=refs_as_dumb)\
                .order_by('article__id', '-created_at')\
                .distinct('article__id')
            included_map = {}
            for item in included:
                included_map[item.full_name] = item.source
            result = []
            new_includes = []
            for ref in include_refs:
                ref_dumb = self._page_name_to_dumb(ref.full_name)
                include_name = articles.normalize_article_name(ref_dumb)
                if include_name in threadvars.get('include_tree', []):
                    print(repr(threadvars.get('include_tree', [])))
                    threadvars.put('include_err', threadvars.get('include_err', []) + [include_name])
                    result.append(ftml.FetchedPage(full_name=ref.full_name, content=None))
                else:
                    result.append(ftml.FetchedPage(full_name=ref.full_name, content=included_map.get(ref_dumb, None)))
                    if include_name not in new_includes:
                        new_includes.append(include_name)
            threadvars.put('include_tree', threadvars.get('include_tree', []) + new_includes)
            return result

        def fetch_internal_links(self, page_refs: list[str]) -> list[ftml.PartialPageInfo]:
            refs_as_dumb = [self._page_name_to_dumb(x) for x in page_refs]
            pages = Article.objects\
                .annotate(dumb_name=Lower(Concat('category', Value(':'), 'name', output_field=TextField())))\
                .filter(dumb_name__in=refs_as_dumb)
            page_map = {}
            for item in pages:
                page_map[item.dumb_name] = item
            result = []
            for ref in page_refs:
                ref_dumb = self._page_name_to_dumb(ref)
                if ref_dumb in page_map:
                    result.append(ftml.PartialPageInfo(full_name=ref, exists=True, title=page_map[ref_dumb].title))
            return result

        def evaluate_expression(self, expr: str) -> any:
            result = expression.evaluate_expression(expr)
            return result

        def normalize_page_name(self, full_name: str) -> str:
            from web.controllers.articles import normalize_article_name
            return normalize_article_name(full_name)

    return CallbacksWithContextImpl(context)


def page_info_from_context(context: RenderContext):
    from web.controllers import articles
    from ftml import ftml

    site = get_current_site()
    return ftml.PageInfo(
        # This is a bit hacky; we just know that "page" and "category" are only used for image URL generation.
        # TODO: fix PageInfo struct to use proper fields
        page=context.source_article.name if context.source_article else '',
        category=context.source_article.category if context.source_article else '',
        site=site.slug,
        domain=site.domain,
        media_domain=site.media_domain,
        tags=articles.get_tags(context.article) if context.article else []
    )


def single_pass_render(source, context=None) -> str:
    from ftml import ftml

    with threadvars.context():
        threadvars.put('include_tree', [])
        threadvars.put('include_err', [])
        html = ftml.render_html(source, callbacks_with_context(context), page_info_from_context(context))
        return SafeString(html.body)


def single_pass_render_with_excerpt(source, context=None) -> [str, str, Optional[str]]:
    from ftml import ftml

    with threadvars.context():
        threadvars.put('include_tree', [])
        threadvars.put('include_err', [])
        html = ftml.render_html(source, callbacks_with_context(context), page_info_from_context(context))
        text = ftml.render_text(source, callbacks_with_context(context), page_info_from_context(context)).body
        text = '\n'.join([x.strip() for x in text.split('\n')])
        text = re.sub(r'\n+', '\n', text)
        if len(text) > 384:
            text = text[:384] + '...'
        return SafeString(html.body), text, None


def single_pass_fetch_backlinks(source, context=None) -> tuple[list[str], list[str]]:
    from ftml import ftml

    text = ftml.collect_backlinks(source, callbacks_with_context(context), page_info_from_context(context))
    return text.included_pages, text.linked_pages
