from . import Node
from ..tokenizer import TokenType


class HTMLLiteralNode(Node):
    starting_token_type = TokenType.OpenHTMLLiteral

    @classmethod
    def parse(cls, p):
        # @< has already been parsed
        content = ''
        while True:
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.CloseHTMLLiteral:
                if '<' in content or '>' in content:
                    return None
                return HTMLLiteralNode(content)
            elif tk.type == TokenType.Null:
                return None
            content += tk.raw

    def __init__(self, text):
        super().__init__()
        self.text = text
        self.force_render = True

    def render(self, context=None):
        return self.text.strip()
