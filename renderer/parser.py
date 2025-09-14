from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model


User = get_user_model()


class RenderContext(object):
    def __init__(self, article=None, source_article=None, path_params=None, user=None):
        self.article = article
        self.source_article = source_article
        self.path_params = path_params or dict()
        self.user = user or AnonymousUser()
        self.title = article.title if article else ''
        self.status = 200
        self.redirect_to = None
        self.add_css = ''
        self.og_description = None
        self.og_image = None

    def clone_with(self, **kwargs):
        article = kwargs.get('article', self.article)
        source_article = kwargs.get('source_article', self.source_article)
        path_params = kwargs.get('path_params', self.path_params)
        user = kwargs.get('user', self.user)
        new_rc = RenderContext(article, source_article, path_params, user)
        new_rc.status = self.status
        new_rc.redirect_to = self.redirect_to
        new_rc.title = self.title
        return new_rc

    def merge(self, other_rc: 'RenderContext'):
        self.status = other_rc.status
        self.redirect_to = other_rc.redirect_to
        self.title = other_rc.title
