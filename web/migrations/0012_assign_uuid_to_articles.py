# Generated by Django 4.0.6 on 2022-08-16 01:16

from django.db import migrations, models
from uuid import uuid4


def assign_uuids(apps, schema_editor):
    Article = apps.get_model("web", "Article")
    db = schema_editor.connection.alias
    for article in Article.objects.using(db).all():
        Article.objects.using(db).filter(id=article.id).update(media_name=uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0011_alter_category_options_article_media_name_and_more'),
    ]

    operations = [
        migrations.RunPython(assign_uuids),
        migrations.AlterField(
            model_name='article',
            name='media_name',
            field=models.TextField(null=False, unique=True, verbose_name='Название папки с файлами в ФС-хранилище'),
        ),
    ]
