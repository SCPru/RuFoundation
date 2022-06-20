from . import Node
from .html_plain import HTMLPlainNode
from ..tokenizer import TokenType


class InlineCodeNode(Node):
    starting_token_type = TokenType.OpenInlineCode

    @classmethod
    def parse(cls, p):
        # {{ has already been parsed
        children = []
        while True:
            pos = p.tokenizer.position
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.CloseInlineCode:
                return HTMLPlainNode('tt', [], children, complex_node=False)
            p.tokenizer.position = pos
            new_children = p.parse_nodes()
            if not new_children:
                return None
            children += new_children
