# Generated by Django 4.0.6 on 2022-08-28 03:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0021_forumthread_created_at_forumthread_deleted_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forumpost',
            name='deleted_at',
        ),
        migrations.RemoveField(
            model_name='forumthread',
            name='deleted_at',
        ),
        migrations.AddField(
            model_name='forumthread',
            name='is_locked',
            field=models.BooleanField(default=False, verbose_name='Закрыто'),
        ),
    ]
