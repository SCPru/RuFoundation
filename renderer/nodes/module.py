from .html import HTMLNode
from .html_base import HTMLBaseNode
import modules


class ModuleNode(HTMLBaseNode):
    # whether this node should be parsed as text (like in module content or code) or subnodes (everything else)
    is_raw_text = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'module'

    @classmethod
    def is_single_tag(cls, _tag, attributes):
        name, _ = HTMLNode.extract_name_from_attributes(attributes)
        return not modules.module_has_content(name)

    def __init__(self, _tag, attributes, content):
        super().__init__()
        name, attributes = HTMLNode.extract_name_from_attributes(attributes)
        self.name = name.lower()
        self.attributes = attributes
        self.content = content
        self.block_node = True

    @staticmethod
    def module_has_content(name):
        name = name.lower()
        content_modules = ['listusers', 'countpages']
        # to-do: remove these hack checks and use only module_has_content (once we have all modules)
        return name in content_modules or modules.module_has_content(name)

    def render(self, context=None):
        # render only module CSS for now
        params = {}
        for attr in self.attributes:
            params[attr[0].lower()] = attr[1]
        try:
            return modules.render_module(self.name, context, params, self.content)
        except modules.ModuleError as e:
            return self.render_template('<div class="error-block"><p>{{error}}</p></div>', error=e.message)
