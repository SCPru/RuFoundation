from .html import HTMLNode
from .html_base import HTMLBaseNode
from django.utils import html


class FontSizeNode(HTMLBaseNode):
    is_single_argument = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'size'

    def __init__(self, _tag, attributes, children):
        super().__init__()
        sz, _ = HTMLNode.extract_name_from_attributes(attributes)
        self.size = sz
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        return ('<span style="font-size: %s">' % html.escape(self.size)) + super().render(context=context) + '</span>'
