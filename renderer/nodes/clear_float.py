from . import Node
from ..tokenizer import TokenType


class ClearFloatNode(Node):
    starting_token_type = TokenType.ClearFloatBeginning

    @classmethod
    def parse(cls, p):
        # ~~~~ has already been parsed.
        # we require that there is either strictly no text or a newline.
        # after this token we should have either more hyphens, >, <, or a newline
        # if anything else, fail
        if not p.check_newline():
            return None
        content = p.read_as_value_until([TokenType.Newline, TokenType.Null])
        content = content.lstrip('~').strip()
        side = 'both'
        if content == '<':
            side = 'left'
        elif content == '>':
            side = 'right'
        elif content:
            return None
        # include newline
        p.tokenizer.skip_whitespace()
        return ClearFloatNode(side)

    def __init__(self, side):
        super().__init__()
        self.side = side
        self.complex_node = True
        self.block_node = True

    def render(self, context=None):
        return self.render_template('<div style="clear: {{side}}"; height: 0; font-size: 1px;"></div>\n', side=self.side)
