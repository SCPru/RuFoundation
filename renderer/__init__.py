from web.models.articles import ArticleVersion
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node
import logging


def get_cached_or_parse_article(version: ArticleVersion):
    if version.ast:
        try:
            root_node = Node.from_json(version.ast)
            return ParseResult(ParseContext(None, root_node), root_node)
        except (TypeError, ValueError):
            pass
    p = Parser(StaticTokenizer(version.source))
    result = p.parse()
    version.ast = result.root.to_json()
    version.save()
    return result


def single_pass_render(source, context=None):
    p = Parser(StaticTokenizer(source))
    result = p.parse()
    s = result.root.render(context)
    return s
