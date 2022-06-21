from . import Node
from .html_plain import HTMLPlainNode
from ..tokenizer import TokenType


class HeadingNode(Node):
    starting_token_type = TokenType.Plus

    @classmethod
    def parse(cls, p):
        # + has already been parsed (one)
        # we require one to 6 + then space then heading text
        # if more than 6, invalid input, fail
        if not p.check_newline():
            return None
        h_count = 1
        while True:
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.Plus:
                h_count += 1
            elif tk.type == TokenType.Whitespace:
                break
            else:
                return None
        if h_count > 6:
            return None
        # parse nodes until newline found
        children = []
        while True:
            tk = p.tokenizer.peek_token()
            if tk.type == TokenType.Null:
                break
            elif tk.type == TokenType.Newline:
                content = HTMLPlainNode('span', [], children)
                return HTMLPlainNode('h%d' % h_count, [], [content])
            new_children = p.parse_nodes()
            if not new_children:
                return None
            children += new_children
