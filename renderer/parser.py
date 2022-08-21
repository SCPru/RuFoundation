from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model


User = get_user_model()


class RenderContext(object):
    def __init__(self, article, source_article, path_params, user):
        self.article = article
        self.source_article = source_article
        self.path_params = path_params
        self.user = user or AnonymousUser()
        self.redirect_to = None
