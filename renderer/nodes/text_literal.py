from .text import TextNode
from ..tokenizer import TokenType


class LiteralNode(TextNode):
    starting_token_type = TokenType.DoubleAt

    @classmethod
    def parse(cls, p):
        # @@ has already been parsed
        content = p.read_as_value_until([TokenType.DoubleAt])
        if content is None:
            return None
        tk = p.tokenizer.read_token()
        if tk.type != TokenType.DoubleAt:
            return None
        return LiteralNode(content)

    def __init__(self, text, literal=False):
        super().__init__(text, literal=True)
