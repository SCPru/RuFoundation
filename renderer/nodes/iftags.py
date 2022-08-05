from .html import HTMLNode
from .html_base import HTMLBaseNode
from web.controllers import articles


class IfTagsNode(HTMLBaseNode):
    is_single_argument = True

    @classmethod
    def is_allowed(cls, tag, _parser):
        return tag == 'iftags'

    def __init__(self, _tag, attributes, children):
        super().__init__()
        condition_raw, _ = HTMLNode.extract_name_from_attributes(attributes)
        self.condition = condition_raw.split(' ')
        self.complex_node = True
        self.block_node = True
        self.paragraphs_set = True
        for child in children:
            self.append_child(child)

    def evaluate_condition(self, context=None):
        # render if condition is true
        # condition = ['+tag1', '-tag2', 'tag3']
        match = False
        article_tags = articles.get_tags(context.article)
        for tag in self.condition:
            if tag.startswith("+") and tag[1:] not in article_tags:
                return False
            elif tag.startswith("-") and tag[1:] in article_tags:
                return False
            else:
                if tag in article_tags:
                    match = True
        return match

    def render(self, context=None):
        if context is None or not self.evaluate_condition(context):
            return ''
        return super().render(context=context)

    def plain_text(self, context=None):
        if context is None or not self.evaluate_condition(context):
            return ''
        return super().plain_text(context=context)
