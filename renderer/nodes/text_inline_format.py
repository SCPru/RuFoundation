from . import Node
from ..tokenizer import TokenType


class TextInlineFormatNode(Node):
    @classmethod
    def wrap_children(cls, children):
        raise RuntimeError("Abstract method not supposed to be called directly")

    @classmethod
    def parse(cls, p):
        # start tag has already been parsed
        if p.check_whitespace(0):
            return None
        children = []
        while True:
            pos = p.tokenizer.position
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.Null:
                return None
            elif tk.type == TokenType.Newline:
                return None
            elif tk.type == cls.starting_token_type:
                if p.check_whitespace(-1):
                    return None
                return cls.wrap_children(children)
            p.tokenizer.position = pos
            new_children = p.parse_nodes()
            if not new_children:
                return None
            children += new_children
