import re

from django.utils.safestring import SafeString

from .nodes.html import HTMLNode
from .nodes.image import ImageNode
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node

from ftml import ftml


def single_pass_render(source, context=None):
    html = ftml.render_html(source)
    html = html['body'] + '<style>' + html['style'] + '</style>'
    return SafeString(html)


def single_pass_render_with_excerpt(source, context=None):
    html = ftml.render_html(source)
    html = html['body'] + '<style>'+html['style']+'</style>'
    text = ftml.render_text(source)
    return SafeString(html), text, None
