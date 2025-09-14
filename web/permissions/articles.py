from web.permissions import BaseRolePermission


def is_perms_collection():
    return True


class ViewArticlesPermission(BaseRolePermission):
    name = 'Просматривать статьи'
    codename = 'view_articles'
    description = 'Позволяет просматривать статьи'
    group = 'Статьи'


class VoteArticlesPermission(BaseRolePermission):
    name = 'Голосовать за статьи'
    codename = 'rate_articles'
    description = 'Позволяет ставить, изменять и снимать оценку со статьи'
    group = 'Статьи'


class CreateArticlesPermission(BaseRolePermission):
    name = 'Создавать статьи'
    codename = 'create_articles'
    description = 'Позволяет создавать статьи'
    group = 'Статьи'


class EditArticlesPermission(BaseRolePermission):
    name = 'Редактировать статьи'
    codename = 'edit_articles'
    description = 'Позволяет изменять содержимое, название статей и откатывать правки'
    group = 'Статьи'


class TagArticlesPermission(BaseRolePermission):
    name = 'Редактировать теги статей'
    codename = 'tag_articles'
    description = 'Позволяет добавлять и удалять теги со статей'
    group = 'Статьи'


class MoveArticlesPermission(BaseRolePermission):
    name = 'Перемещать статьи'
    codename = 'move_articles'
    description = 'Позволяет изменять адрес и категорию статей'
    group = 'Статьи'


class LockArticlesPermission(BaseRolePermission):
    name = 'Блокировать статьи'
    codename = 'lock_articles'
    description = 'Позволяет устанавливать и снимать блокировку со статей'
    group = 'Статьи'


class ManageArticleFilesPermission(BaseRolePermission):
    name = 'Редактировать файлы статей'
    codename = 'manage_articles_files'
    description = 'Позволяет загружать, переименовывать и удалять файлы статей'
    group = 'Статьи'


class DeleteArticlesPermission(BaseRolePermission):
    name = 'Удалять статьи'
    codename = 'delete_articles'
    description = 'Позволяет безвозвратно удалять статьи'
    group = 'Статьи'


class ResetArticleVotesPermission(BaseRolePermission):
    name = 'Сбрасывать голоса'
    codename = 'reset_article_votes'
    description = 'Позволяет сбрасывать голоса статей'
    group = 'Статьи'


class CommentArticlesPermission(BaseRolePermission):
    name = 'Обсуждать статьи'
    codename = 'comment_articles'
    description = 'Позволяет обсуждать статьи'
    group = 'Статьи'


class ViewArticlesCommentsPermission(BaseRolePermission):
    name = 'Просматривать обсуждения статей'
    codename = 'view_articles_comments'
    description = 'Позволяет просматривать обсуждения статей'
    group = 'Статьи'
