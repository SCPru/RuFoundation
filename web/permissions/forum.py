from web.permissions import BaseRolePermission


is_perms_collection = True


class ViewForumPostsPermission(BaseRolePermission):
    name = 'Просматривать посты на форуме'
    codename = 'view_forum_posts'
    description = 'Позволяет просматривать посты на форуме'
    group = 'Форум'


class CreateForumPostsPermission(BaseRolePermission):
    name = 'Создавать посты на форуме'
    codename = 'create_forum_posts'
    description = 'Позволяет создавать посты на форуме'
    group = 'Форум'


class EditForumPostsPermission(BaseRolePermission):
    name = 'Редактировать посты на форуме'
    codename = 'edit_forum_posts'
    description = 'Позволяет редактировать чужие посты на форуме'
    group = 'Форум'


class DeleteForumPostsPermission(BaseRolePermission):
    name = 'Удалять посты на форуме'
    codename = 'delete_forum_posts'
    description = 'Позволяет удалять посты на форуме'
    group = 'Форум'


class ViewForumThreadsPermission(BaseRolePermission):
    name = 'Просматривать ветки форума'
    codename = 'view_forum_threads'
    description = 'Позволяет просматривать ветки форума'
    group = 'Форум'


class CreateForumThreadsPermission(BaseRolePermission):
    name = 'Создавать ветки форума'
    codename = 'create_forum_threads'
    description = 'Позволяет создавать ветки форума'
    group = 'Форум'


class EditForumThreadsPermission(BaseRolePermission):
    name = 'Редактировать ветки форума'
    codename = 'edit_forum_threads'
    description = 'Позволяет редактировать название и описание ветки форума'
    group = 'Форум'


class PinForumThreadsPermission(BaseRolePermission):
    name = 'Закреплять ветки форума'
    codename = 'pin_forum_threads'
    description = 'Позволяет закреплять ветки форума'
    group = 'Форум'


class LockForumThreadsPermission(BaseRolePermission):
    name = 'Блокировать ветки форума'
    codename = 'lock_forum_threads'
    description = 'Позволяет блокировать ветки форума'
    group = 'Форум'


class MoveForumThreadsPermission(BaseRolePermission):
    name = 'Перемещать ветки форума'
    codename = 'move_forum_threads'
    description = 'Позволяет перемещать ветки форума'
    group = 'Форум'


class ViewForumSectionsPermission(BaseRolePermission):
    name = 'Просматривать разделы форума'
    codename = 'view_forum_sections'
    description = 'Позволяет просматривать разделы форума'
    group = 'Форум'


class ViewHiddenForumSectionsPermission(BaseRolePermission):
    name = 'Просматривать скрытые разделы форума'
    codename = 'view_hidden_forum_sections'
    description = 'Позволяет просматривать скрытые разделы форума'
    group = 'Форум'


class ViewForumCategoriesPermission(BaseRolePermission):
    name = 'Просматривать категории форума'
    codename = 'view_forum_categories'
    description = 'Позволяет просматривать категории форума'
    group = 'Форум'
