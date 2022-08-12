from . import Node


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
        text = self.text
        if not self.literal:
            text = text.replace('--', '—').replace('<<', '«').replace('>>', '»')
        if self.literal and self.force_render:
            return self.render_template('<span style="white-space: pre-wrap">{{text}}</span>', text=text)
        return text

    def plain_text(self, context=None):
        text = self.text
        if not self.literal:
            text = self.text.replace('--', '—').replace('<<', '«').replace('>>', '»')
        return text
