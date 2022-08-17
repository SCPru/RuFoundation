import re

from django.utils.safestring import SafeString

from .nodes.html import HTMLNode
from .nodes.image import ImageNode
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node

from ftml import ftml


class CallbacksWithContext(ftml.Callbacks):
    def __init__(self, context):
        super().__init__()
        self.context = context

    def module_has_body(self, module_name: str) -> bool:
        print('called body %s' % module_name)
        return False

    def render_module(self, module_name: str, params: dict[str, str], body: str) -> str:
        print('called render %s' % module_name)
        return ''


def single_pass_render(source, context=None):
    html = ftml.render_html(source, CallbacksWithContext(context))
    html = html['body'] + '<style>' + html['style'] + '</style>'
    return SafeString(html)


def single_pass_render_with_excerpt(source, context=None):
    html = ftml.render_html(source, CallbacksWithContext(context))
    html = html['body'] + '<style>'+html['style']+'</style>'
    text = ftml.render_text(source, CallbacksWithContext(context))
    return SafeString(html), text, None
