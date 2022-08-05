from . import Node
from .html_base import HTMLBaseNode


class FootnoteNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'footnote'

    def __init__(self, _tag, _attributes, children):
        super().__init__()
        for child in children:
            self.append_child(child)

    def render_footnote(self, context=None):
        return super().render(context)

    def get_number(self):
        all_footnotes = Node.find_nodes_recursively(self.root, FootnoteNode)
        for i in range(len(all_footnotes)):
            if all_footnotes[i] == self:
                return i+1
        return 0

    def render(self, context=None):
        return self.render_template(
            '<sup class="footnoteref"><a id="footnoteref={{number}}" class="footnoteref w-footnoteref" href="#footnote-{{number}}">{{number}}</a></sup>',
            number=self.get_number()
        )

    def plain_text(self, context=None):
        return '(%s)' % super().plain_text(context=context)
