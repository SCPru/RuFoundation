from . import Node
from .align_marker import AlignMarkerNode
from django.utils import html


class ParagraphNode(Node):
    def __init__(self, children):
        super().__init__()
        self.block_node = True
        self.collapsed = False
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        content = super().render(context=context)
        if (self.children and self.children[0].complex_node) or self.collapsed:
            return content
        if len(self.children) == 1 and self.children[0].force_render:
            return content
        alignattr = ''
        if self.children and isinstance(self.children[0], AlignMarkerNode):
            alignattr = ' style="text-align: %s"' % (html.escape(self.children[0].align))
        return ('<p%s>' % alignattr) + content + '</p>'