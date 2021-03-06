from web.models.articles import ArticleVersion
from .parser import Parser, ParseResult, ParseContext
from .tokenizer import StaticTokenizer
from .nodes import Node
import logging
import time
from django.conf import settings


def get_cached_or_parse_article(version: ArticleVersion):
    if version.ast and not settings.DEBUG:
        try:
            root_node = Node.from_json(version.ast)
            logging.info('returning existing AST for %s', version.article.full_name)
            return ParseResult(ParseContext(None, root_node), root_node)
        except (TypeError, ValueError):
            pass
    t = time.time()
    p = Parser(StaticTokenizer(version.source))
    result = p.parse()
    version.ast = result.root.to_json()
    version.save()
    t2 = time.time()
    logging.info('parsing of new AST for %s took %.2fs', version.article.full_name, t2-t)
    return result


def single_pass_render(source, context=None):
    p = Parser(StaticTokenizer(source))
    result = p.parse()
    s = result.root.render(context)
    return s
