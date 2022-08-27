from django.contrib.auth.models import AnonymousUser

from system.models import User
from web.models.articles import Article, Category
from web.models.forum import ForumSection, ForumCategory, ForumThread, ForumPost


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

        case (_, 'comment', Article(category=category)):
            return _get_or_default_category(category).users_can_comment

        case (_, 'delete', Article(category=category)):
            return _get_or_default_category(category).users_can_delete

        case (_, 'view', ForumSection(is_hidden_for_users=True)):
            return False

        case (_, 'view', ForumCategory(section=section)):
            return check(user, 'view', section)

        case (_, 'view', ForumThread(category=None, article=article)):
            return check(user, 'comment', article)

        case (_, 'view', ForumThread(article=None, category=category)):
            return check(user, 'view', category)

        case (user, 'edit', ForumThread(author=author)) if author == user:
            return True

        case (user, 'delete', ForumThread(author=author)) if author == user:
            return True

        # This should not be checked often -- it's going to be quite heavy
        case (_, 'view', ForumPost(thread=thread)):
            return check(user, 'view', thread)

        case (user, 'edit', ForumPost(author=author)) if author == user:
            return True

        case (user, 'delete', ForumPost(author=author)) if author == user:
            return True

        case (_, _, _):
            return False


def _get_or_default_category(category):
    cat = Category.objects.filter(name=category)
    if not cat:
        return Category(name=category)
    else:
        return cat[0]
