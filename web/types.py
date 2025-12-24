__all__ = [
    '_UserType',
    '_FullNameOrArticle',
    '_FullNameOrCategory',
    '_FullNameOrTag',
    '_UserIdOrUser',
]

from typing import Optional, Union

from django.contrib.auth.models import AnonymousUser

from web.models.articles import Article, Category, Tag
from web.models.users import User


_UserType = Optional[Union[User, AnonymousUser]]
_FullNameOrArticle = Optional[Union[str, Article]]
_FullNameOrCategory = Optional[Union[str, Category]]
_FullNameOrTag = Optional[Union[str, Tag]]
_UserIdOrUser = Optional[Union[int, User]]