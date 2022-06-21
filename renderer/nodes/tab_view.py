from .html_base import HTMLBaseNode
from .tab_view_tab import TabViewTabNode
from django.utils import html


class TabViewNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'tabview'

    def __init__(self, _tag, attributes, children):
        super().__init__()
        self.attributes = attributes
        self.block_node = True
        self.complex_node = True
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        code = '<div class="yui-navset yui-navset-top w-tabview">'
        code += '  <ul class="yui-nav">'
        tab = 0
        for child in self.children:
            if not isinstance(child, TabViewTabNode):
                continue
            name = child.name
            child.visible = (tab == 0)
            # sadly complete absence of spaces is needed for wikidot compatibility
            code += '<li class="selected" title="active">' if child.visible else '<li>'
            code += '<a href="javascript:;">'
            code += '<em>' + html.escape(name) + '</em>'
            code += '</a>'
            code += '</li>'
            tab += 1
        code += '  </ul>'
        code += '  <div class="yui-content">'
        code += super().render(context=context)
        code += '  </div>'
        code += '</div>'
        return code
