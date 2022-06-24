# Generated by Django 4.0.4 on 2022-06-21 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0002_alter_article_site_alter_articlelogentry_site_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='article',
            options={'permissions': [('can_vote_article', 'Может голосовать за статью'), ('can_lock_article', 'Может заблокировать страницу для правок')], 'verbose_name': 'Статья', 'verbose_name_plural': 'Статьи'},
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'permissions': [('add_article_in_category', 'Может добавлять новые статьи в категорию'), ('change_article_in_category', 'Может изменять статьи в категории'), ('delete_article_in_category', 'Может удалять статьи в категории'), ('can_vote_article_in_category', 'Может голосовать за статьи в категории'), ('can_lock_article_in_category', 'Может заблокировать страницу для правок в категории')], 'verbose_name': 'Категория', 'verbose_name_plural': 'Категории'},
        ),
        migrations.AddField(
            model_name='article',
            name='locked',
            field=models.BooleanField(default=False, verbose_name='Страница защищена'),
        ),
    ]