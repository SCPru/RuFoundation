import re

from .link import LinkNode
from ..tokenizer import TokenType


class ExternalLinkNode(LinkNode):
    starting_token_type = TokenType.OpenSingleBracket

    @classmethod
    def parse(cls, p):
        # [ has already been parsed
        p.tokenizer.skip_whitespace()
        url = ''
        is_text = False
        text = ''
        while True:
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.CloseSingleBracket:
                blank = False
                # wikidot does not do links if they do not have a slash
                if '/' not in url and '#' not in url:
                    return None
                if url[0:1] == '*':
                    blank = True
                    url = url[1:]
                return ExternalLinkNode(url, text.strip(), blank=blank)
            elif tk.type == TokenType.Null:
                return None
            if not is_text:
                if tk.type == TokenType.Whitespace:
                    is_text = True
                    # wikidot does not do links if they do not have a slash
                    if '/' not in url and '#' not in url:
                        return None
                else:
                    url += tk.raw
            else:
                text += tk.raw

    def __init__(self, url, text, blank):
        super().__init__(url, text, blank=blank)
