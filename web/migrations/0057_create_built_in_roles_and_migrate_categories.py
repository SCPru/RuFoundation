from django.apps.registry import Apps
from django.db import migrations
from django.db.models import Max



def create_built_in_roles(apps: Apps, schema_editor):
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
        profile_visual_mode='status',
        group_votes=True,
        index=last_index+2,
    )
    editor_role = Role.objects.create(
        slug='editor',
        name='Участник',
        category=category,
        votes_title='Голоса участников',
        profile_visual_mode='status',
        group_votes=True,
        index=last_index+1
    )

    reader_role.users.set(User.objects.filter(is_active=True, is_editor=False))
    editor_role.users.set(User.objects.filter(is_active=True, is_editor=True))
    
    for user in User.objects.all():
        if user.is_editor:
            user.vote_set.all().filter(role__isnull=True).update(role=editor_role)
        else:
            user.vote_set.all().filter(role__isnull=True).update(role=reader_role)

    registered_role = Role.objects.get(slug='registered')
    everyone_role = Role.objects.get(slug='everyone')

    registered_role.index = last_index+3
    everyone_role.index = last_index+4

    registered_role.save()
    everyone_role.save()


def migrate_categories(apps: Apps, schema_editor):
    RolePermissionsOverride = apps.get_model('web', 'RolePermissionsOverride')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Category = apps.get_model('web', 'Category')
    Role = apps.get_model('web', 'Role')

    content_type, _ = ContentType.objects.get_or_create(
        app_label='web',
        model='roles'
    )

    def get_permission(codename):
        return Permission.objects.get(
            codename=codename,
            content_type=content_type
        )

    reader_role = Role.objects.get(slug='reader')
    editor_role = Role.objects.get(slug='editor')

    for category in Category.objects.all():
        reader_perms = []
        reader_restrs = []
        editor_perms = []
        editor_restrs = []

        if category.readers_can_comment:
            reader_perms.append(get_permission('comment_articles'))
        else:
            reader_restrs.append(get_permission('comment_articles'))

        if category.readers_can_create:
            reader_perms.append(get_permission('create_articles'))
        else:
            reader_restrs.append(get_permission('create_articles'))

        if category.readers_can_delete:
            reader_perms.append(get_permission('delete_articles'))
        else:
            reader_restrs.append(get_permission('delete_articles'))

        if category.readers_can_edit:
            reader_perms.append(get_permission('edit_articles'))
        else:
            reader_restrs.append(get_permission('edit_articles'))

        if category.readers_can_rate:
            reader_perms.append(get_permission('rate_articles'))
        else:
            reader_restrs.append(get_permission('rate_articles'))

        if category.readers_can_view:
            reader_perms.append(get_permission('view_articles'))
        else:
            reader_restrs.append(get_permission('view_articles'))

        if category.users_can_comment:
            editor_perms.append(get_permission('comment_articles'))
        else:
            editor_restrs.append(get_permission('comment_articles'))

        if category.users_can_create:
            editor_perms.append(get_permission('create_articles'))
        else:
            editor_restrs.append(get_permission('create_articles'))

        if category.users_can_delete:
            editor_perms.append(get_permission('delete_articles'))
        else:
            editor_restrs.append(get_permission('delete_articles'))

        if category.users_can_edit:
            editor_perms.append(get_permission('edit_articles'))
        else:
            editor_restrs.append(get_permission('edit_articles'))

        if category.users_can_rate:
            editor_perms.append(get_permission('rate_articles'))
        else:
            editor_restrs.append(get_permission('rate_articles'))

        if category.users_can_view:
            editor_perms.append(get_permission('view_articles'))
        else:
            editor_restrs.append(get_permission('view_articles'))

        if reader_perms or reader_restrs:
            perms_override = RolePermissionsOverride.objects.create(role=reader_role)
            perms_override.permissions.add(*reader_perms)
            perms_override.restrictions.add(*reader_restrs)
            category.permissions_override.add(perms_override)

        if editor_perms or editor_restrs:
            perms_override = RolePermissionsOverride.objects.create(role=editor_role)
            perms_override.permissions.add(*editor_perms)
            perms_override.restrictions.add(*editor_restrs)
            category.permissions_override.add(perms_override)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('web', '0056_create_roles_and_more'),
    ]

    operations = [
        # Create roles for readers and editors
        migrations.RunPython(create_built_in_roles, migrations.RunPython.noop),

        # Migrate permissions in categories
        migrations.RunPython(migrate_categories, migrations.RunPython.noop),
    ]
