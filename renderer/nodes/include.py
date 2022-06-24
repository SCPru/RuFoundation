from .html import HTMLNode
from .html_base import HTMLBaseNode
from ..parser import Parser
from ..tokenizer import StaticTokenizer
from web.controllers import articles
from web import threadvars
import re


class IncludeNode(HTMLBaseNode):
    # allows having | between attrs
    pipe_separated_attributes = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'include'

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return True

    def __init__(self, _tag, attributes, _nothing):
        super().__init__()
        name, _ = HTMLNode.extract_name_from_attributes(attributes)
        self.name = name
        self.attributes = attributes
        self.complex_node = True
        self.code = None
        # if this article was already included, fail
        if self.name in threadvars.get('include_tree', []):
            return
        article = articles.get_article(self.name)
        if article is not None:
            code = articles.get_latest_source(article) or ''
            map_values = dict()
            for name, value in self.attributes:
                if name not in map_values or (map_values[name].startswith('{$') and map_values[name].endswith('}')):
                    map_values[name] = value
            for name in map_values:
                if type(map_values[name]) != str:
                    continue
                code = re.sub(r'{\$%s}' % re.escape(name), map_values[name], code, flags=re.IGNORECASE)
            parse_context = threadvars.get('parser_context')
            threadvars.put('include_tree', threadvars.get('include_tree', []) + [self.name])
            nodes = Parser(StaticTokenizer(code), context=parse_context).parse().root.children
            threadvars.put('include_tree', [x for x in threadvars.get('include_tree', []) if x != self.name])
            for node in nodes:
                self.append_child(node)

    def render(self, context=None):
        # Include is never rendered directly unless it's broken
        if not self.children:
            return self.render_template(
                """
                <div class="error-block">
                    <p>
                        Вставленная страница &quot;{{name}}&quot; не существует (<a href="/{{name}}/edit/true" target="_blank">создать её сейчас</a>)
                    </p>
                </div>
                """,
                name=self.name
            )
        else:
            return super().render(context=context)
