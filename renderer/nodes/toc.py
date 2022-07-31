from .heading import HeadingNode
from .html import HTMLNode
from .html_base import HTMLBaseNode
import modules
from . import Node


class ModuleNode(HTMLBaseNode):
    # whether this node should be parsed as text (like in module content or code) or subnodes (everything else)
    is_raw_text = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'toc'

    @classmethod
    def is_single_tag(cls, _tag, _attributes):
        return True

    def __init__(self, _tag, _attributes, _content):
        super().__init__()
        self.block_node = True
        self.complex_node = True
        self.headings = []

    def pre_render(self, context=None):
        nodes = Node.find_nodes_recursively(self.root, HeadingNode)
        headings = []
        i = 0
        for node in nodes:
            headings.append({'level': '%dem' % ((node.level - 1) * 2), 'title': node.plain_text(context=context), 'toc_id': i})
            node.toc_id = i
            i += 1
        self.headings = headings

    def render(self, context=None):
        print(repr(self.headings))
        return self.render_template(
            """
            <table style="margin: 0; padding: 0">
                <tbody>
                <tr>
                    <td style="margin: 0; padding: 0">
                        <div id="toc" class="w-toc">
                            <div id="toc-action-bar">
                                <a href="#" style="display: none" class="w-toc-hide">Свернуть</a>
                                <a href="#" class="w-toc-show">Раскрыть</a>
                            </div>
                            <div class="title">Содержание</div>
                            <div id="toc-list" class="w-toc-content" style="display: none">
                                {% for item in toc %}
                                    <div style="margin-left: {{ item.level }}">
                                        <a href="#toc{{ item.toc_id }}">{{ item.title }}</a>
                                    </div>
                                {% endfor %}
                            </div>
                        </div>
                    </td>
                </tr>
                </tbody>
            </table>
            """,
            toc=self.headings
        )
