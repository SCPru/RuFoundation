from . import Node
from ..tokenizer import TokenType
import re


class ColorNode(Node):
    starting_token_type = TokenType.DoubleHash

    @classmethod
    def parse(cls, p):
        # ## has already been parsed
        p.tokenizer.skip_whitespace()
        color = p.read_as_value_until([TokenType.Pipe])
        if color is None:
            return None
        p.tokenizer.skip_whitespace()
        tk = p.tokenizer.read_token()
        if tk.type != TokenType.Pipe:
            return None
        children = []
        while True:
            pos = p.tokenizer.position
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.DoubleHash:
                return ColorNode(color, children)
            elif tk.type == TokenType.Null:
                return None
            p.tokenizer.position = pos
            new_children = p.parse_nodes()
            if not new_children:
                return None
            children += new_children

    def __init__(self, color, children):
        super().__init__()
        self.color = color
        for child in children:
            self.append_child(child)

    def render(self, context=None):
        color = self.color
        if not color.startswith('#') and re.match(r'^([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$', color):
            color = '#' + color
        return self.render_template('<span style="color: {{color}}">{{content}}</span>', color=color, content=super().render(context=context))
