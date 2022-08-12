from .html_plain import HTMLPlainNode
from .text_inline_format import TextInlineFormatNode
from ..tokenizer import TokenType


class TextInlineFormatEmNode(TextInlineFormatNode):
    starting_token_type = TokenType.DoubleSlash

    @classmethod
    def wrap_children(cls, children):
        return HTMLPlainNode('em', [], children)
