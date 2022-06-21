from .list import ListNode
from ..tokenizer import TokenType


class ListUlNode(ListNode):
    starting_token_type = TokenType.Asterisk

    @classmethod
    def parse(cls, p, lstype='ul'):
        return super().parse(p, lstype)
