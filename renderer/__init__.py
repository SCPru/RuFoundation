import logging
import re

from django.db.models import TextField, Value
from django.db.models.functions import Concat
from django.utils.safestring import SafeString

import modules
from system.models import User
from web.controllers import articles
from web.models.articles import ArticleVersion, Article
from web.models.sites import get_current_site
from .nodes.html import HTMLNode
from .nodes.image import ImageNode
from .parser import Parser, ParseResult, ParseContext, RenderContext
from .tokenizer import StaticTokenizer
from .nodes import Node

from ftml import ftml

import time

from .utils import render_user_to_html, render_template_from_string

USE_RUST = True


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
    def _page_name_to_dumb(page_name):
        category, name = articles.get_name(page_name)
        return '%s:%s' % (category, name)

    def fetch_includes(self, include_refs: list[ftml.IncludeRef]) -> list[ftml.FetchedPage]:
        refs_as_dumb = [self._page_name_to_dumb(x.full_name) for x in include_refs]
        included = ArticleVersion.objects\
            .select_related('article')\
            .annotate(full_name=Concat('article__category', Value(':'), 'article__name', output_field=TextField()))\
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


def page_info_from_context(context: RenderContext):
    site = get_current_site()
    return ftml.PageInfo(
        page=context.source_article.name,
        category=context.source_article.category,
        site=site.slug,
        domain=site.domain,
        media_domain=site.media_domain
    )


def single_pass_render(source, context=None):
    if USE_RUST:
        t1 = time.time()
        html = ftml.render_html(source, CallbacksWithContext(context), page_info_from_context(context))
        t2 = time.time()
        if context.article == context.source_article:
            print('rendering %s took %.2fs' % (context.source_article, t2-t1))
        html = html['body'] + '<style>' + html['style'] + '</style>'
        return SafeString(html)
    else:
        t1 = time.time()
        p = Parser(StaticTokenizer(source))
        result = p.parse()
        s = result.root.render(context)
        t2 = time.time()
        if context.article == context.source_article:
            print('rendering %s took %.2fs' % (context.source_article, t2 - t1))
        return s


def single_pass_render_with_excerpt(source, context=None):
    if USE_RUST:
        t1 = time.time()
        html = ftml.render_html(source, CallbacksWithContext(context), page_info_from_context(context))
        html = html['body'] + '<style>'+html['style']+'</style>'
        text = ftml.render_text(source, CallbacksWithContext(context), page_info_from_context(context))
        t2 = time.time()
        if context.article == context.source_article:
            print('rendering %s with text took %.2fs' % (context.source_article, t2 - t1))
        return SafeString(html), text, None
    else:
        t1 = time.time()
        p = Parser(StaticTokenizer(source))
        result = p.parse()
        s, plain_text = result.root.render_with_plain_text(context)
        plain_text = re.sub(r'\n+', '\n\n', plain_text)
        if len(plain_text) > 256:
            plain_text = plain_text[:256].strip() + '...'
        image_nodes = Node.find_nodes_recursively(result.root, ImageNode)
        image = None
        for node in image_nodes:
            if HTMLNode.get_attribute(node.attributes, 'featured', None):
                image = node.get_image_url(context)
        t2 = time.time()
        if context.article == context.source_article:
            print('rendering %s with text took %.2fs' % (context.source_article, t2 - t1))
        return s, plain_text, image
