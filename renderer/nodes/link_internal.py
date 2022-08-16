from django.db.models.functions import Concat
from django.db.models import Q, Value as V, F, Count, Sum, TextField

from web.models.articles import Article
from . import Node
from .link import LinkNode
from ..tokenizer import TokenType
from web.controllers import articles
from web import threadvars


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

    def __init__(self, article, text):
        external = False
        if '#' in article:
            article, hashtag = article.split('#', 1)
            hashtag = '#' + hashtag
        else:
            hashtag = ''
        article_id = articles.normalize_article_name(article.lower().strip())
        article_url = '/' + article_id + hashtag
        if '/' in article:
            external = True
            article_url = article + hashtag
            article_id = None
        self.article_id = article_id
        self.external = external
        self.original_text = text
        super().__init__(article_url, text, exists=True)

    @staticmethod
    def fetch_articles_by_names(names):
        names = list(dict.fromkeys([('_default:%s'%x).lower() if ':' not in x else x.lower() for x in names]))
        all_articles = Article.objects.annotate(f_full_name=Concat('category', V(':'), 'name', output_field=TextField())).filter(f_full_name__in=names)
        articles_dict = dict()
        for article in all_articles:
            articles_dict[article.full_name.lower()] = article
        return articles_dict

    def pre_render(self, context=None):
        render_globals = threadvars.get('render_globals')
        if 'link_internal_articles' not in render_globals:
            items = Node.find_nodes_recursively(self.root, InternalLinkNode)
            names = []
            for item in items:
                name = item.article_id
                if not name:
                    continue
                names.append(name)
            articles_dict = self.fetch_articles_by_names(names)
            render_globals['link_internal_articles'] = articles_dict
        else:
            articles_dict = render_globals['link_internal_articles']
        article_obj = articles_dict.get(self.article_id.lower()) if not self.external else None
        self.exists = self.external or (article_obj is not None)
        text = self.original_text
        if not text:
            if self.external:
                text = self.url
            else:
                if article_obj is not None:
                    text = article_obj.title.strip() or self.article_id
                else:
                    text = self.article_id
        self.text = text
