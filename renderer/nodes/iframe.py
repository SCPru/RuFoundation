from .html import HTMLNode
from .html_base import HTMLBaseNode


class IframeNode(HTMLBaseNode):
    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'iframe'

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return True

    def __init__(self, _tag, attributes, _children):
        super().__init__()
        url, attributes = HTMLNode.extract_name_from_attributes(attributes)
        self.url = url
        self.attributes = attributes
        self.complex_node = True
        self.block_node = True

    def render(self, context=None):
        return '<div><!--Iframe is not supported yet--></div>'
