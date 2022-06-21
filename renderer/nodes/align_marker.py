from . import Node
from ..tokenizer import TokenType


class AlignMarkerNode(Node):
    starting_token_type = TokenType.Equals

    @classmethod
    def parse(cls, p):
        # = has already been parsed
        if not p.check_newline():
            return None

        return AlignMarkerNode('center')

    def __init__(self, align):
        super().__init__()
        self.align = align

    def render(self, context=None):
        return ''
