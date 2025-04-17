# Generated by Django 5.1.4 on 2025-04-17 21:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0047_subscribe_users'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserNotificationTemplate',
        ),
        migrations.AlterField(
            model_name='usernotification',
            name='type',
            field=models.TextField(choices=[('welcome', 'Приветственное сообщение'), ('new_post_reply', 'Ответ на пост'), ('new_thread_post', 'Новый пост'), ('new_article_revision', 'Правка статьи')], verbose_name='Тип уведомления'),
        ),
    ]
