from .parser import Parser
from .tokenizer import Tokenizer
import time
import json


def single_pass_render(source, context=None):
    t = time.time()
    p = Parser(Tokenizer(source))
    result = p.parse()
    debug = True
    if context is not None and context.source_article == context.article and debug:
        print('rendering took %.3fs' % (time.time()-t))
        print('rendering tree')
        print(json.dumps(result.root.to_json()))
    return result.root.render(context)
