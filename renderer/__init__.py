from .parser import Parser
from .tokenizer import StaticTokenizer
import time
import json


def single_pass_render(source, context=None):
    t = time.time()
    p = Parser(StaticTokenizer(source))
    result = p.parse()
    debug = False
    if context is not None and context.source_article == context.article:
        print('rendering took %.3fs (%s)' % (time.time()-t, context.source_article.full_name))
        if debug:
            print('rendering tree')
            print(json.dumps(result.root.to_json()))
    return result.root.render(context)
