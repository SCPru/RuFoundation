from . import Node
from ..tokenizer import TokenType


class HorizontalRulerNode(Node):
    starting_token_type = TokenType.HrBeginning

    @classmethod
    def parse(cls, p):
        # ---- has already been parsed.
        # we require that there is either strictly no text or a newline.
        # after this token we should have either more hyphens or a newline
        # if anything else, fail
        if not p.check_newline():
            return None
        content = p.read_as_value_until([TokenType.Newline, TokenType.Null])
        if content is None or content.rstrip().replace('-', '') != '':
            return None
        # include newline
        p.tokenizer.skip_whitespace()
        return HorizontalRulerNode()

    def __init__(self):
        super().__init__()
        self.complex_node = True
        self.block_node = True

    def render(self, context=None):
        return self.render_template('<hr>')
