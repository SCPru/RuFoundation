from .parser import Parser
from .tokenizer import Tokenizer


def single_pass_render(source, context_article=None):
    p = Parser(Tokenizer(source))
    return p.parse().render(context_article)
