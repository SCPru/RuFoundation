import re

from django.utils.safestring import SafeString

import modules
from .nodes.html import HTMLNode
from .nodes.image import ImageNode
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node

from ftml import ftml

import time


class CallbacksWithContext(ftml.Callbacks):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def module_has_body(self, module_name: str) -> bool:
        return modules.module_has_content(module_name.lower())

    def render_module(self, module_name: str, params: dict[str, str], body: str) -> str:
        return modules.render_module(module_name, self.context, params, content=body)


def single_pass_render(source, context=None):
    t1 = time.time()
    html = ftml.render_html(source, CallbacksWithContext(context))
    t2 = time.time()
    print('rendering %s took %.2fs' % (context.source_article, t2-t1))
    html = html['body'] + '<style>' + html['style'] + '</style>'
    return SafeString(html)


def single_pass_render_with_excerpt(source, context=None):
    t1 = time.time()
    html = ftml.render_html(source, CallbacksWithContext(context))
    t2 = time.time()
    print('rendering %s took %.2fs' % (context.source_article, t2 - t1))
    html = html['body'] + '<style>'+html['style']+'</style>'
    text = ftml.render_text(source, CallbacksWithContext(context))
    return SafeString(html), text, None
