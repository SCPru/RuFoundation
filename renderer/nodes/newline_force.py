from . import Node
from ..tokenizer import TokenType


class NewlineForceNode(Node):
    starting_token_type = TokenType.Underline

    @classmethod
    def parse(cls, p):
        tk = p.tokenizer.read_token()
        if tk.type != TokenType.Newline:
            return None
        return NewlineForceNode()

    def __init__(self):
        super().__init__()

    def render(self, context=None):
        return self.render_template('<br>')
