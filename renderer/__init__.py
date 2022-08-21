import re
from typing import Optional

from django.db.models import TextField, Value
from django.db.models.functions import Concat, Lower
from django.utils.safestring import SafeString

import modules
from system.models import User
from web.models.articles import ArticleVersion, Article
from web.models.sites import get_current_site
from .parser import RenderContext
from .utils import render_user_to_html, render_template_from_string

from ftml import ftml


class CallbacksWithContext(ftml.Callbacks):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def module_has_body(self, module_name: str) -> bool:
        return modules.module_has_content(module_name.lower())

    def render_module(self, module_name: str, params: dict[str, str], body: str) -> str:
        params_for_module = {key.lower(): value for (key, value) in params.items()}
        return modules.render_module(module_name, self.context, params_for_module, content=body)

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
        # this must return Wiki markup because of the stage it runs at.
        return '[[div class="error-block"]]Вставленная страница "%s" не существует ([[a href="/%s/edit/true" target="_blank"]]создать её сейчас[[/a]])[[/div]]' % (full_name, full_name)

    # This function converts magical _default category to explicit _default category
    # This is so that we can later reuse this in the database query that will just concat the category+name for articles
    @staticmethod
    def _page_name_to_dumb(name):
        return ('_default:%s' % name).lower() if ':' not in name else name.lower()

    def fetch_includes(self, include_refs: list[ftml.IncludeRef]) -> list[ftml.FetchedPage]:
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
        for ref in include_refs:
            ref_dumb = self._page_name_to_dumb(ref.full_name)
            result.append(ftml.FetchedPage(full_name=ref.full_name, content=included_map.get(ref_dumb, None)))
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


def page_info_from_context(context: RenderContext):
    site = get_current_site()
    return ftml.PageInfo(
        page=context.source_article.name,
        category=context.source_article.category,
        site=site.slug,
        domain=site.domain,
        media_domain=site.media_domain
    )


def single_pass_render(source, context=None) -> str:
    html = ftml.render_html(source, CallbacksWithContext(context), page_info_from_context(context))
    return SafeString(html.body)


def single_pass_render_with_excerpt(source, context=None) -> [str, str, Optional[str]]:
    html = ftml.render_html(source, CallbacksWithContext(context), page_info_from_context(context))
    text = ftml.render_text(source, CallbacksWithContext(context), page_info_from_context(context)).body
    text = '\n'.join([x.strip() for x in text.split('\n')])
    text = re.sub(r'\n+', '\n', text)
    if len(text) > 384:
        text = text[:384] + '...'
    return SafeString(html.body), text, None


def single_pass_fetch_backlinks(source, context=None) -> tuple[list[str], list[str]]:
    text = ftml.render_text(source, CallbacksWithContext(context), page_info_from_context(context))
    return text.included_pages, text.linked_pages
