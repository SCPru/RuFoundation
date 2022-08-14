import ast
import operator as op

from . import Node
from .expression import ExpressionNode
from .text import TextNode
from ..tokenizer import TokenType


class ExpressionBlockNode(ExpressionNode):
    starting_token_type = TokenType.OpenDoubleBracket

    @classmethod
    def parse(cls, p):
        # this is like ExpressionNode, but syntax is different
        # [[if ...]] (or [[ifexpr]])
        # [[else]]
        # [[/if]]
        allowed_expr_types = ['if', 'ifexpr']
        t = p.tokenizer.read_token()
        if t.type != TokenType.String or t.value.lower() not in allowed_expr_types:
            return None
        expr_type = t.value.lower()
        p.tokenizer.skip_whitespace()
        condition = p.read_as_value_until([TokenType.Pipe, TokenType.CloseDoubleBracket])
        if condition is None:
            return None
        condition = condition.strip()
        t = p.tokenizer.read_token()
        if t.type != TokenType.CloseDoubleBracket:
            return None
        true_case = []
        false_case = []
        is_true = True
        while True:
            t = p.tokenizer.peek_token()
            if t.type == TokenType.OpenDoubleBracket:
                pos = p.tokenizer.position
                p.tokenizer.position += 1
                p.tokenizer.skip_whitespace()
                t2 = p.tokenizer.read_token()
                if t2.type == TokenType.String and t2.value == 'else' and is_true:
                    p.tokenizer.skip_whitespace()
                    t3 = p.tokenizer.read_token()
                    if t3.type == TokenType.CloseDoubleBracket:
                        is_true = False
                        continue
                elif t2.type == TokenType.Slash:
                    p.tokenizer.skip_whitespace()
                    t3 = p.tokenizer.read_token()
                    if t3.type == TokenType.String and t3.value.lower() == expr_type:
                        p.tokenizer.skip_whitespace()
                        t4 = p.tokenizer.read_token()
                        if t4.type == TokenType.CloseDoubleBracket:
                            break
                p.tokenizer.position = pos
            children = p.parse_nodes()
            if not children:
                return None
            if is_true:
                true_case += children
            else:
                false_case += children
        return cls(expr_type, condition, true_case, false_case)
