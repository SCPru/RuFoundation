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


USE_RUST = True


class CallbacksWithContext(ftml.Callbacks):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def module_has_body(self, module_name: str) -> bool:
        return modules.module_has_content(module_name.lower())

    def render_module(self, module_name: str, params: dict[str, str], body: str) -> str:
        return modules.render_module(module_name, self.context, params, content=body)


def single_pass_render(source, context=None):
    if USE_RUST:
        t1 = time.time()
        html = ftml.render_html(source, CallbacksWithContext(context))
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
        html = ftml.render_html(source, CallbacksWithContext(context))
        t2 = time.time()
        if context.article == context.source_article:
            print('rendering %s with text took %.2fs' % (context.source_article, t2 - t1))
        html = html['body'] + '<style>'+html['style']+'</style>'
        text = ftml.render_text(source, CallbacksWithContext(context))
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
