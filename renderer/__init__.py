from .parser import Parser
from .tokenizer import Tokenizer
import time
import json


def single_pass_render(source, context=None):
    t = time.time()
    p = Parser(Tokenizer(source))
    result = p.parse().root.render(context)
    #print('rendering took %.3fs' % (time.time()-t))
    #print('rendering tree')
    #print(json.dumps(p.parse().to_json()))
    return result
