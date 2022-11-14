import ast
import operator as op


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
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval_ast(node.operand))
    elif isinstance(node, ast.Module):  # root
        if len(node.body) != 1:
            raise TypeError(node)
        return _eval_ast(node.body[0])
    elif isinstance(node, ast.Expr):  # expr
        return _eval_ast(node.value)
    elif isinstance(node, ast.Call):  # function. allowed functions: min, max, abs
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
            if len(args) != 1:
                raise ValueError(args)
            return round(args[0])
        elif id == 'lower':
            if len(args) != 1 or not isinstance(args[0], str):
                raise ValueError(args)
            return args[0].lower()
        elif id == 'upper':
            if len(args) != 1 or not isinstance(args[0], str):
                raise ValueError(args)
            return args[0].upper()
        else:
            raise ValueError(id)
    else:
        raise TypeError(node)


def evaluate_expression(expression):
    try:
        return _eval_ast(ast.parse(expression))
    except:
        return None
