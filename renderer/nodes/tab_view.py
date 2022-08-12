from .html_base import HTMLBaseNode
from .tab_view_tab import TabViewTabNode


class TabViewNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'tabview'

    def __init__(self, _tag, attributes, children):
        super().__init__()
        self.attributes = attributes
        self.block_node = True
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        tabs = []
        tab = 0
        for child in self.children:
            if not isinstance(child, TabViewTabNode):
                continue
            child.visible = (tab == 0)
            tab += 1
            tabs.append(child)

        # HTML one-liner is required for proper appearance
        return self.render_template(
            """
            <div class="yui-navset yui-navset-top w-tabview">
                <ul class="yui-nav">{% for tab in tabs %}<li{% if tab.visible %} class="selected" title="active"{% endif %}><a href="javascript:;"><em>{{tab.name}}</em></a></li>{% endfor %}</ul>
                <div class="yui-content">
                {{content}}
                </div>
            </div>
            """,
            tabs=tabs,
            content=super().render(context=context)
        )
