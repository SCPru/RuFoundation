from .html_plain import HTMLPlainNode
from .text_inline_format import TextInlineFormatNode
from ..tokenizer import TokenType


class TextInlineFormatStrikeNode(TextInlineFormatNode):
    starting_token_type = TokenType.DoubleDash

    @classmethod
    def wrap_children(cls, children):
        return HTMLPlainNode('strike', [], children, complex_node=False)
