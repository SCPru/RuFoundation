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

        render_footnotes = []
        for i in range(len(footnotes)):
            render_footnotes.append({
                'number': i+1,
                'content': footnotes[i].render_footnote()
            })

        return self.render_template(
            """
            <div class="footnotes-footer">
                <div class="title">{{title}}</div>
                {% for footnote in footnotes %}
                <div id="footnote-{{footnote.number}}" class="footnote-footer">
                    <a href="#footnoteref-{{footnote.number}}">{{footnote.number}}</a>. {{footnote.content}}
                </div>
                {% endfor %}
            </div>
            """,
            title=HTMLNode.get_attribute(self.attributes, 'title', 'Сноски'),
            footnotes=render_footnotes
        )
