from . import Node
from .footnote import FootnoteNode
from .html import HTMLNode
from .html_base import HTMLBaseNode


class FootnoteBlockNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'footnoteblock'

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return True

    def __init__(self, _tag, attributes, _nothing):
        super().__init__()
        self.attributes = attributes

    def get_footnotes(self):
        return Node.find_nodes_recursively(self.root, FootnoteNode)

    def render(self, context=None):
        footnotes = self.get_footnotes()
        if not len(footnotes):
            return ''
        output = '<div class="footnotes-footer">'
        output += '<div class="title">%s</div>' % HTMLNode.get_attribute(self.attributes, 'title', 'Сноски')
        for i in range(len(footnotes)):
            output += '<div id="footnote-%d" class="footnote-footer">' % (i+1)
            output += '<a href="#footnoteref-%d">%d</a>. ' % (i+1, i+1)
            output += footnotes[i].render_footnote(context)
            output += '</div>'
        output += '</div>'
        return output
