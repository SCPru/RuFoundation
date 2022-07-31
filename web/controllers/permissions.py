from django.contrib.auth.models import AnonymousUser

from system.models import User
from web.models.articles import Article, Category


def check(user, action, obj):
    match (user, action, obj):
        case (User(is_superuser=True) | User(is_staff=True), _, _):
            return True

        case (AnonymousUser(), perm, _) if perm != 'view':
            return False

        case (_, perm, Article(locked=True)) if perm != 'view':
            return False

        case (_, 'view', Article(category=category)):
            return _get_or_default_category(category).users_can_view

        case (_, 'create', Article(category=category)):
            return _get_or_default_category(category).users_can_create

        case (_, 'edit', Article(category=category)):
            return _get_or_default_category(category).users_can_edit

        case (_, 'rate', Article(category=category)):
            return _get_or_default_category(category).users_can_rate

        case (_, 'delete', Article(category=category)):
            return _get_or_default_category(category).users_can_delete

        case (_, _, _):
            return False


def _get_or_default_category(category):
    cat = Category.objects.filter(name=category)
    if not cat:
        return Category(name=category)
    else:
        return cat[0]
