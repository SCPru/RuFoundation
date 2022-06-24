from . import Node
from ..tokenizer import TokenType


class CommentNode(Node):
    starting_token_type = TokenType.OpenComment

    @classmethod
    def parse(cls, p):
        # [!-- has already been parsed
        content = ''
        while True:
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.CloseComment:
                return CommentNode(content)
            else:
                content += tk.raw

    def __init__(self, text):
        super().__init__()
        self.text = text

    def render(self, context=None):
        #return '<!-- %s -->' % html.escape(self.text)
        # This is actually not rendered
        return ''
