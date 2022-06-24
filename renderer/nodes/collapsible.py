from .html import HTMLNode
from .html_base import HTMLBaseNode


class CollapsibleNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'collapsible'

    def __init__(self, _tag, attributes, children):
        super().__init__()
        self.attributes = attributes
        self.block_node = True
        self.complex_node = True
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        return self.render_template(
            """
            <div class="w-collapsible collapsible-block">
                <div class="collapsible-block-folded" style="display: block">
                    <a class="collapsible-block-link" href="javascript:;">
                        {{show_text}}
                    </a>
                </div>
                <div class="collapsible-block-unfolded" style="display: none">
                    <div class="collapsible-block-unfolded-link">
                        <a class="collapsible-block-link" href="javascript:;">
                            {{hide_text}}
                        </a>
                    </div>
                    <div class="collapsible-block-content">
                        {{content}}
                    </div>
                </div>
            </div>
            """,
            show_text=HTMLNode.get_attribute(self.attributes, 'show', '+ открыть блок'),
            hide_text=HTMLNode.get_attribute(self.attributes, 'hide', '- закрыть блок'),
            content=super().render(context=context)
        )

