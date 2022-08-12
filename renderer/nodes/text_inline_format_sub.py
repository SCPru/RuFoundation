from .html_plain import HTMLPlainNode
from .text_inline_format import TextInlineFormatNode
from ..tokenizer import TokenType


class TextInlineFormatSubNode(TextInlineFormatNode):
    starting_token_type = TokenType.DoubleSub

    @classmethod
    def wrap_children(cls, children):
        return HTMLPlainNode('sub', [], children)
