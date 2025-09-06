from django.db import migrations
from django.db.models import Max


def create_built_in_roles(apps, schema_editor):
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
