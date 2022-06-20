from .list import ListNode
from ..tokenizer import TokenType


class ListOlNode(ListNode):
    starting_token_type = TokenType.Hash

    @classmethod
    def parse(cls, p, lstype='ol'):
        return super().parse(p, lstype)
