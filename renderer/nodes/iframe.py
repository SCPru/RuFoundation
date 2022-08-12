from .html import HTMLNode
from .html_base import HTMLBaseNode
from .link import LinkNode


class IframeNode(HTMLBaseNode):
    is_first_single_argument = True

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
        attrs = HTMLNode.render_attributes(self.attributes, ['class', 'id', 'style', 'align', 'frameborder', 'width', 'height', 'scrolling'])
        return self.render_template(
            '<iframe src="{{src}}" sandbox="allow-scripts allow-top-navigation allow-popups" {{attrs}}></iframe>',
            src=LinkNode.filter_url(self.url),
            attrs=attrs
        )
