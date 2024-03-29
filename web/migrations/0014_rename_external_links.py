# Generated by Django 4.0.6 on 2022-08-16 01:55

from django.db import migrations
import sys


def get_full_name(article):
    if article.category == '_default':
        return article.name
    else:
        return '%s:%s' % (article.category, article.name)


def rename_external_links(apps, schema_editor):
    Article = apps.get_model("web", "Article")
    ArticleLogEntry = apps.get_model("web", "ArticleLogEntry")
    ExternalLink = apps.get_model("web", "ExternalLink")
    db = schema_editor.connection.alias
    first_log = False
    for article in Article.objects.using(db).all():
        # find renames, if any.
        renames = ArticleLogEntry.objects.using(db).filter(article=article, type='name').order_by('-rev_number')
        old_name = get_full_name(article)
        new_name = old_name
        for rename in renames:
            if old_name == rename.meta['name']:
                old_name = rename.meta['prev_name']
            else:
                raise ValueError('Integrity error: expected rename to be %s, found %s instead' % (old_name, rename.meta['name']))
        if new_name != old_name:
            if not first_log:
                print('\n', end='')
                first_log = True
            if len(ExternalLink.objects.using(db).filter(link_from__iexact=new_name)):
                print('    skip (collision, do manually): %s -> %s\n    ' % (old_name, new_name), end='')
                sys.stdout.flush()
            else:
                print('    update: %s -> %s\n    ' % (old_name, new_name), end='')
                sys.stdout.flush()
                ExternalLink.objects.using(db).filter(link_from__iexact=old_name).update(link_from=new_name)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0013_rename_media_folders'),
    ]

    operations = [
        migrations.RunPython(rename_external_links)
    ]
