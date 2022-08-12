from .html_plain import HTMLPlainNode
from .text_inline_format import TextInlineFormatNode
from ..tokenizer import TokenType


class TextInlineFormatUnderlineNode(TextInlineFormatNode):
    starting_token_type = TokenType.DoubleUnderline

    @classmethod
    def wrap_children(cls, children):
        return HTMLPlainNode('u', [], children)
