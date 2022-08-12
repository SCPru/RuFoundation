import ast
import operator as op

from . import Node
from .text import TextNode
from ..tokenizer import TokenType


class ExpressionNode(Node):
    starting_token_type = TokenType.OpenDoubleBracket

    @classmethod
    def parse(cls, p):
        # [[ has already been parsed.
        # after this we should have `#` and then either ifexpr, expr, or if
        # then there is | for true case and | for false case
        t = p.tokenizer.read_token()
        if t.type != TokenType.Hash:
            return None
        allowed_expr_types = ['if', 'ifexpr', 'expr']
        t = p.tokenizer.read_token()
        if t.type != TokenType.String or t.value.lower() not in allowed_expr_types:
            print(repr(t))
            return None
        expr_type = t.value.lower()
        p.tokenizer.skip_whitespace()
        condition = p.read_as_value_until([TokenType.Pipe, TokenType.CloseDoubleBracket])
        if condition is None:
            return None
        condition = condition.strip()
        t = p.tokenizer.read_token()
        if t.type == TokenType.CloseDoubleBracket and expr_type == 'expr':
            return ExpressionNode(expr_type, condition, [], [])
        if t.type != TokenType.Pipe:
            return None
        true_case = []
        false_case = []
        is_true = True
        while True:
            t = p.tokenizer.peek_token()
            if t.type == TokenType.Pipe:
                p.tokenizer.position += 1
                if is_true:
                    is_true = False
                    continue
                else:
                    return None  # invalid syntax
            elif t.type == TokenType.CloseDoubleBracket:
                p.tokenizer.position += 1
                break
            children = p.parse_nodes()
            if not children:
                return None
            if is_true:
                true_case += children
            else:
                false_case += children
        return ExpressionNode(expr_type, condition, true_case, false_case)

    @classmethod
    def _eval_ast(cls, node):
        operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                     ast.Div: op.truediv, ast.BitXor: op.xor,
                     ast.USub: op.neg, ast.Eq: op.eq, ast.Lt: op.lt, ast.Gt: op.gt,
                     ast.LtE: op.le, ast.GtE: op.ge, ast.NotEq: op.ne}

        if isinstance(node, ast.Constant):  # number or string or w/e
            return node.value
        elif isinstance(node, ast.Compare):  # x == y
            items = [node.left] + node.comparators
            for i in range(len(node.ops)):
                if not operators[type(node.ops[i])](cls._eval_ast(items[i]), cls._eval_ast(items[i+1])):
                    return False
            return True
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return operators[type(node.op)](cls._eval_ast(node.left), cls._eval_ast(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return operators[type(node.op)](cls._eval_ast(node.operand))
        elif isinstance(node, ast.Module):  # root
            if len(node.body) != 1:
                raise TypeError(node)
            return cls._eval_ast(node.body[0])
        elif isinstance(node, ast.Expr):  # expr
            return cls._eval_ast(node.value)
        elif isinstance(node, ast.Call):  # function. allowed functions: min, max, abs
            if len(node.keywords):
                raise ValueError(node.keywords)
            id = node.func.id.lower()
            args = [cls._eval_ast(x) for x in node.args]
            if id == 'min':
                return min(*args)
            elif id == 'max':
                return max(*args)
            elif id == 'abs':
                if len(args) != 1:
                    raise ValueError(args)
                return abs(args[0])
            else:
                raise ValueError(id)
        else:
            raise TypeError(node)

    @classmethod
    def evaluate_expression(cls, expression):
        try:
            return cls._eval_ast(ast.parse(expression))
        except:
            return None

    def __init__(self, expr_type, expression, true_case, false_case):
        super().__init__()
        self.expr_type = expr_type
        self.complex_node = False
        self.block_node = False
        # since all expressions here are static, we can evaluate it right away. this saves on renderer hacks.
        if self.expr_type == 'if':
            if expression != 'false' and expression != 'null' and expression:
                for child in true_case:
                    self.append_child(child)
            else:
                for child in false_case:
                    self.append_child(child)
        elif self.expr_type == 'expr':
            result = self.evaluate_expression(expression)
            if result is None:
                result = ''
            else:
                result = str(result)
            self.append_child(TextNode(result, literal=True))
        elif self.expr_type == 'ifexpr':
            result = self.evaluate_expression(expression)
            if result:
                for child in true_case:
                    self.append_child(child)
            else:
                for child in false_case:
                    self.append_child(child)
