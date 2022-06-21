from .html_plain import HTMLPlainNode
from .text_inline_format import TextInlineFormatNode
from ..tokenizer import TokenType


class TextInlineFormatStrongNode(TextInlineFormatNode):
    starting_token_type = TokenType.DoubleAsterisk

    @classmethod
    def wrap_children(cls, children):
        return HTMLPlainNode('strong', [], children, complex_node=False)
