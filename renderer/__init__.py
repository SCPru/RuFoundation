import re

from django.utils.safestring import SafeString

from .nodes.html import HTMLNode
from .nodes.image import ImageNode
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node

from ftml import ftml


def single_pass_render(source, context=None):
    return SafeString(ftml.render_html(source))


def single_pass_render_with_excerpt(source, context=None):
    html = ftml.render_html(source)
    text = ftml.render_text(source)
    return SafeString(html), text, None
