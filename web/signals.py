from django.contrib.auth.models import Permission

from web.models.roles import Role
from web.permissions import get_role_permissions_content_type


def after_migration(migration):
    if migration == '0057':
        assign_default_permissions()


def assign_default_permissions():
    readers_perms = ['rate_articles', 'comment_articles', 'create_forum_threads', 'create_forum_posts']
    editors_perms = ['create_articles', 'edit_articles', 'tag_articles', 'move_articles', 'manage_article_files', 'reset_article_votes']
    everyone_perms = ['view_articles', 'view_forum_sections', 'view_forum_categories', 'view_forum_threads', 'view_forum_posts']

    content_type = get_role_permissions_content_type()

    Role.objects.get(slug='everyone').permissions.set(Permission.objects.filter(codename__in=everyone_perms, content_type=content_type))
    Role.objects.get(slug='reader').permissions.set(Permission.objects.filter(codename__in=readers_perms, content_type=content_type))
    Role.objects.get(slug='editor').permissions.set(Permission.objects.filter(codename__in=editors_perms, content_type=content_type))
