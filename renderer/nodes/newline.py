from . import Node
from ..tokenizer import TokenType


class NewlineNode(Node):
    starting_token_type = TokenType.Newline

    @classmethod
    def parse(cls, p):
        return NewlineNode()

    def __init__(self, force_render=False):
        super().__init__()
        self.block_node = True
        self.force_render = force_render

    def render(self, context=None):
        return '<br>'
