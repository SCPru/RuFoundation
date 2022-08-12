from .html import HTMLNode
from .html_base import HTMLBaseNode


class TabViewTabNode(HTMLBaseNode):
    is_single_argument = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'tab'

    def __init__(self, _tag, attributes, children):
        super().__init__()
        name, _ = HTMLNode.extract_name_from_attributes(attributes)
        self.name = name
        self.block_node = True
        self.visible = False
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        return self.render_template(
            '<div class="w-tabview-tab" style="display: {% if visible %}block{% else %}none{% endif %}">{{content}}</div>',
            visible=self.visible,
            content=super().render(context=context)
        )
