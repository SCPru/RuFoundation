from .html import HTMLNode
from .html_base import HTMLBaseNode


class HTMLPlainNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return HTMLNode.node_allowed(tag)

    def __init__(self, name, attributes, children, trim_paragraphs=False):
        super().__init__()

        name_remap = {
            'row': 'tr',
            'hcell': 'th',
            'cell': 'td'
        }

        if name in name_remap:
            name = name_remap[name]

        self.name = name
        self.attributes = attributes
        self.trim_paragraphs = trim_paragraphs or self.name in ['th', 'td']
        self.block_node = self.name in ['div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'th', 'td', 'li', 'ul', 'ol']
        self.paragraphs_set = self.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'tr', 'th', 'td', 'li', 'ul', 'ol']
        for child in children:
            # if this is a table, we should not allow _anything_ that is not table structure
            # otherwise invalid <br>'s are produced (and more)
            if self.name == 'table' and (not isinstance(child, HTMLPlainNode) or child.name != 'tr'):
                continue
            elif self.name == 'tr' and (not isinstance(child, HTMLPlainNode) or child.name not in ['th', 'td']):
                continue
            elif self.name == 'li' and (not isinstance(child, HTMLPlainNode) or child.name not in ['ol', 'ul']):
                continue
            self.append_child(child)

    def render(self, context=None):
        content = super().render(context=context)
        attr_whitelist = ['class', 'id', 'style']
        if self.name == 'a':
            attr_whitelist.append('href')
            attr_whitelist.append('target')
        elif self.name == 'th' or self.name == 'td':
            attr_whitelist.append('colspan')
            attr_whitelist.append('rowspan')
        attr_string = HTMLNode.render_attributes(self.attributes, attr_whitelist)
        return self.render_template('<{{tag}}{{attrs}}>{{content}}</{{tag}}>', tag=self.name, attrs=attr_string, content=content)
