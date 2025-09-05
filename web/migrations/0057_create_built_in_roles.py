import auto_prefetch
import django.db.models.deletion
import django.db.models.manager
import web.fields.models
import web.models.roles

from django.db import migrations, models
from django.db.models import Max


def create_built_in_roles(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    RoleCategory = apps.get_model('web', 'RoleCategory')
    Role = apps.get_model('web', 'Role')
    User = apps.get_model('web', 'User')

    last_index = Role.objects.aggregate(max_index=Max('index'))['max_index']

    category = RoleCategory.objects.create(
        name='Статус пользователя'
    )

    reader_role = Role.objects.create(
        slug='reader',
        name='Читатель',
        category=category,
        votes_title='Голоса читателей',
        group_votes=True,
        index=last_index+2,
    )
    editor_role = Role.objects.create(
        slug='editor',
        name='Участник',
        category=category,
        votes_title='Голоса участников',
        group_votes=True,
        index=last_index+1
    )

    content_type, _ = ContentType.objects.get_or_create(
        app_label='web',
        model='roles'
    )

    readers_perms = ['rate_articles', 'comment_articles', 'create_forum_threads', 'create_forum_posts']
    editors_perms = ['create_articles', 'edit_articles', 'tag_articles', 'move_articles', 'manage_article_files', 'reset_article_votes']

    reader_role.permissions.set(Permission.objects.filter(codename__in=readers_perms, content_type=content_type))
    editor_role.permissions.set(Permission.objects.filter(codename__in=editors_perms, content_type=content_type))

    reader_role.users.set(User.objects.filter(is_active=True))
    editor_role.users.set(User.objects.filter(is_active=True, is_editor=True))
    
    for user in User.objects.filter(is_active=True):
        if user.is_editor:
            user.vote_set.all().filter(role__isnull=True).update(role=editor_role)
        else:
            user.vote_set.all().filter(role__isnull=True).update(role=reader_role)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('web', '0056_rolecategory_remove_vote_visual_group_and_more'),
    ]

    operations = [
        # Create roles for readers and editors
        migrations.RunPython(create_built_in_roles, migrations.RunPython.noop),
    ]
