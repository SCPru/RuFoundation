from .html_base import HTMLBaseNode
from .tab_view_tab import TabViewTabNode


class CodeNode(HTMLBaseNode):
    # whether this node should be parsed as text (like in module content or code) or subnodes (everything else)
    is_raw_text = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'code'

    def __init__(self, _tag, attributes, content):
        super().__init__()
        self.attributes = attributes
        self.block_node = True
        self.complex_node = True
        self.content = content

    def render(self, context=None):
        # The way it works originally is that empty newline at beginning and end is stripped if any
        # HTML one-liner is required for proper appearance
        return self.render_template(
            """
            <div class="code">
                <div class="hl-main">
                    <pre>{{content}}</pre>
                </div>
            </div>
            """,
            content=self.content
        )
