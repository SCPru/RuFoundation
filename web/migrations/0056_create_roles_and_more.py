import auto_prefetch
import django.db.models.deletion
import django.db.models.manager
import web.fields.models
import web.models.roles

from django.db import migrations, models
from django.apps.registry import Apps



def create_default_roles(apps: Apps, schema_editor):
    Role = apps.get_model('web', 'Role')
    Role.objects.create(
        slug='everyone',
        index=0
    )
    Role.objects.create(
        slug='registered',
        index=0
    )

def visualgroups_to_roles(apps: Apps, schema_editor):
    VisualUserGroup = apps.get_model('web', 'VisualUserGroup')
    Role = apps.get_model('web', 'Role')
    Vote = apps.get_model('web', 'Vote')
    User = apps.get_model('web', 'User')

    new_roles = []
    for n, group in enumerate(VisualUserGroup.objects.all().order_by('index')):
        new_roles.append(Role(
            slug=f'migrated_role_{n}',
            name=group.name,
            index=n,
            group_votes=True,
            inline_visual_mode='badge' if group.show_badge else 'hidden',
            profile_visual_mode='status',
            badge_text=group.badge,
            badge_bg=group.badge_bg,
            badge_text_color=group.badge_text_color,
            badge_show_border=group.badge_show_border,
        ))

    Role.objects.bulk_create(new_roles)

    for user in User.objects.filter(visual_group__isnull=False):
        user.roles.add(Role.objects.get(name=user.visual_group.name))

    votes_to_update = []
    for vote in Vote.objects.filter(visual_group__isnull=False):
        vote.role = Role.objects.get(name=vote.visual_group.name)
        votes_to_update.append(vote)

    Vote.objects.bulk_update(votes_to_update, ['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('web', '0055_alter_articlesearchindex_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoleCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Категория ролей',
                'verbose_name_plural': 'Категории ролей',
            },
        ),
        migrations.AlterField(
            model_name='forumsection',
            name='is_hidden_for_users',
            field=models.BooleanField(default=False, verbose_name='Видна только модераторам'),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(unique=True, verbose_name='Идентификатор')),
                ('name', models.CharField(blank=True, verbose_name='Полное название')),
                ('short_name', models.CharField(blank=True, verbose_name='Короткое название')),
                ('index', models.PositiveIntegerField(db_index=True, default=0, editable=False, verbose_name='Приоритет')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Доступ в админку')),
                ('group_votes', models.BooleanField(default=False, verbose_name='Группировать голоса')),
                ('votes_title', models.CharField(blank=True, verbose_name='Подпись группы голосов')),
                ('inline_visual_mode', models.CharField(choices=[('hidden', 'Скрыто'), ('badge', 'Бейдж'), ('icon', 'Иконка')], default='hidden', verbose_name='Режим отображения в имени')),
                ('profile_visual_mode', models.CharField(choices=[('hidden', 'Скрыто'), ('badge', 'Бейдж'), ('status', 'Статус')], default='hidden', verbose_name='Режим отображения в профиле')),
                ('color', web.fields.models.CSSColorField(default='#000000', verbose_name='Цвет')),
                ('icon', models.FileField(blank=True, upload_to='-/roles', validators=[web.models.roles.svg_file_validator], verbose_name='Иконка')),
                ('badge_text', models.CharField(blank=True, verbose_name='Текст бейджа')),
                ('badge_bg', web.fields.models.CSSColorField(default='#808080', verbose_name='Цвет бейджа')),
                ('badge_text_color', web.fields.models.CSSColorField(default='#ffffff', verbose_name='Цвет текста')),
                ('badge_show_border', models.BooleanField(default=False, verbose_name='Показывать границу')),
                ('permissions', models.ManyToManyField(blank=True, related_name='role_permissions_set', to='auth.permission', verbose_name='Разрешения')),
                ('restrictions', models.ManyToManyField(blank=True, related_name='role_restrictions_set', to='auth.permission', verbose_name='Запрещения')),
                ('category', auto_prefetch.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.rolecategory', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Роль',
                'verbose_name_plural': 'Роли',
                'ordering': ['index'],
                'abstract': False,
                'base_manager_name': 'prefetch_manager',
            },
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('prefetch_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ManyToManyField(blank=True, related_name='users', related_query_name='user', to='web.role', verbose_name='Роли'),
        ),
        migrations.AddField(
            model_name='vote',
            name='role',
            field=auto_prefetch.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='web.role', verbose_name='Роль'),
        ),
        migrations.CreateModel(
            name='RolePermissionsOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permissions', models.ManyToManyField(blank=True, related_name='override_role_permissions_set', to='auth.permission')),
                ('restrictions', models.ManyToManyField(blank=True, related_name='override_role_restrictions_set', to='auth.permission')),
                ('role', auto_prefetch.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.role')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'prefetch_manager',
            },
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('prefetch_manager', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='category',
            name='permissions_override',
            field=models.ManyToManyField(to='web.rolepermissionsoverride'),
        ),

        # Create default roles
        migrations.RunPython(create_default_roles, migrations.RunPython.noop, atomic=True),

        # Migrate from visual user groups to roles
        migrations.RunPython(visualgroups_to_roles, migrations.RunPython.noop, atomic=True),
    ]
