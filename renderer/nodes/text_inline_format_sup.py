from .html_plain import HTMLPlainNode
from .text_inline_format import TextInlineFormatNode
from ..tokenizer import TokenType


class TextInlineFormatSupNode(TextInlineFormatNode):
    starting_token_type = TokenType.DoubleSup

    @classmethod
    def wrap_children(cls, children):
        return HTMLPlainNode('sup', [], children, complex_node=False)
