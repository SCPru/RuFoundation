from .html import HTMLNode
from .html_base import HTMLBaseNode


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
        return self.render_template('<span style="font-size: {{size}}">{{content}}</span>', size=self.size, content=super().render(context=context))

