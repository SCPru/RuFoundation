from . import Node
from django.utils import html


class TextNode(Node):
    def __init__(self, text, literal=False):
        super().__init__()
        self.text = text
        self.literal = literal
        self.force_render = literal and text and text.strip(' ') != '\n'

    @staticmethod
    def is_literal(node):
        return isinstance(node, TextNode) and node.literal

    def render(self, context=None):
        # very special logic
        text = html.escape(self.text).replace('--', '&mdash;').replace('&lt;&lt;', '&laquo;').replace('&gt;&gt;', '&raquo;')
        if self.literal and self.force_render:
            return '<span style="white-space: pre-wrap">' + text + '</span>'
        return text
