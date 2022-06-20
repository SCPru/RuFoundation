from . import Node
from ..tokenizer import TokenType


class NewlineEscapeNode(Node):
    starting_token_type = TokenType.Backslash

    @classmethod
    def parse(cls, p):
        tk = p.tokenizer.read_token()
        if tk.type != TokenType.Newline:
            return None
        return NewlineEscapeNode()

    def __init__(self):
        super().__init__()

    def render(self, context=None):
        return ''
