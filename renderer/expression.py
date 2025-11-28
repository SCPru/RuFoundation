import ast
import operator as op
from math import ceil, floor, sin, cos, tan, asin, acos, atan, sqrt, pow
from random import randint


def _eval_ast(node):
    operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                 ast.Div: op.truediv, ast.BitXor: op.xor,
                 ast.USub: op.neg, ast.Eq: op.eq, ast.Lt: op.lt, ast.Gt: op.gt,
                 ast.LtE: op.le, ast.GtE: op.ge, ast.NotEq: op.ne}

    if isinstance(node, ast.Constant):  # number or string or w/e
        return node.value
    elif isinstance(node, ast.Compare):  # x == y
        items = [node.left] + node.comparators
        for i in range(len(node.ops)):
            if not operators[type(node.ops[i])](_eval_ast(items[i]), _eval_ast(items[i + 1])):
                return False
        return True
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    elif isinstance(node, ast.BoolOp):  # <values> <operator>
        evaluated_values = [_eval_ast(x) for x in node.values]
        if isinstance(node.op, ast.And):
            return len([x for x in evaluated_values if not x]) == 0
        elif isinstance(node.op, ast.Or):
            return len([x for x in evaluated_values if x]) > 0
        raise ValueError(node.op)
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval_ast(node.operand))
    elif isinstance(node, ast.Module):  # root
        if len(node.body) != 1:
            raise TypeError(node)
        return _eval_ast(node.body[0])
    elif isinstance(node, ast.Expr):  # expr
        return _eval_ast(node.value)
    elif isinstance(node, ast.Call):  # function
        if len(node.keywords):
            raise ValueError(node.keywords)
        id = node.func.id.lower()
        args = [_eval_ast(x) for x in node.args]
        if id == 'min':
            return min(*args)
        elif id == 'max':
            return max(*args)
        elif id == 'abs':
            if len(args) != 1:
                raise ValueError(args)
            return abs(args[0])
        elif id == 'round':
            if len(args) not in [1, 2]:
                raise ValueError(args)
            return round(args[0], args [1] if len(args) == 2 else 0)
        elif id == 'ceil':
            if len(args) != 1:
                raise ValueError(args)
            return ceil(args[0])
        elif id == 'floor':
            if len(args) != 1:
                raise ValueError(args)
            return floor(args[0])
        elif id == 'div':
            if len(args) != 2:
                raise ValueError(args)
            return args[0] // args[1]
        elif id == 'random':
            if len(args) != 2:
                raise ValueError(args)
            return randint(args[0], args[1])
        elif id in ['sin', 'cos', 'tan', 'asin', 'acos', 'atan']:
            if len(args) != 1:
                raise ValueError(args)
            f = {'sin': sin, 'cos': cos, 'tan': tan, 'asin': asin, 'acos': acos, 'atan': atan}
            return f[id][args[0]]
        elif id == 'sqrt':
            if len(args) != 1:
                raise ValueError(args)
            return sqrt(args[0])
        elif id == 'pow':
            if len(args) != 2:
                raise ValueError(args)
            return pow(args[0], args[1])
        elif id == 'unset':
            if len(args) != 1:
                raise ValueError(args)
            s = str(args[0])
            return s.startswith('%%') and s.endswith('%%')
        elif id == 'len':
            if len(args) != 1 or not isinstance(args[0], str):
                raise ValueError(args)
            return len(args[0])
        elif id == 'lower':
            if len(args) != 1 or not isinstance(args[0], str):
                raise ValueError(args)
            return args[0].lower()
        elif id == 'upper':
            if len(args) != 1 or not isinstance(args[0], str):
                raise ValueError(args)
            return args[0].upper()
        elif id == 'substr':
            if len(args) not in [2, 3] or not isinstance(args[0], str):
                raise ValueError(args)
            return args[0][ args[1] : args[2] if len(args) == 3 else None]
        else:
            raise ValueError(id)
    else:
        raise TypeError(node)


def evaluate_expression(expression):
    try:
        return _eval_ast(ast.parse(expression))
    except:
        return None
