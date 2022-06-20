from .link import LinkNode
from ..tokenizer import TokenType
from web.controllers import articles


class InternalLinkNode(LinkNode):
    starting_token_type = TokenType.OpenTripleBracket

    @classmethod
    def parse(cls, p):
        # [[[ has already been parsed
        p.tokenizer.skip_whitespace()
        article = p.read_as_value_until([TokenType.CloseTripleBracket, TokenType.Pipe])
        if article is None:
            return None
        tk = p.tokenizer.read_token()
        if tk.type == TokenType.CloseTripleBracket:
            # title = article name
            return InternalLinkNode(article, article)
        elif tk.type != TokenType.Pipe:
            return None
        text = ''
        while True:
            tk = p.tokenizer.read_token()
            if tk.type == TokenType.CloseTripleBracket:
                return InternalLinkNode(article, text.strip())
            elif tk.type == TokenType.Null:
                return None
            text += tk.raw

    @staticmethod
    def article_exists(article):
        return articles.get_article(article) is not None

    def __init__(self, article, text):
        external = False
        article_id = articles.normalize_article_name(article.lower().strip())
        article_url = '/' + article_id
        if '/' in article:
            external = True
            article_url = article
            article_id = ''
        article_obj = None
        if not text:
            if external:
                text = article_url
            else:
                article_obj = articles.get_article(article)
                if article_obj is not None:
                    text = article_obj.title
                else:
                    text = article
        super().__init__(article_url, text, exists=article_obj is not None or external)
