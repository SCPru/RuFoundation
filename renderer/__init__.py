import re

from .nodes.html import HTMLNode
from .nodes.image import ImageNode
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node


def single_pass_render(source, context=None):
    p = Parser(StaticTokenizer(source))
    result = p.parse()
    s = result.root.render(context)
    return s


def single_pass_render_with_excerpt(source, context=None):
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
    return s, plain_text, image
