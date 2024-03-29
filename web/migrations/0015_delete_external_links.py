# Generated by Django 4.0.6 on 2022-08-16 02:04

import sys

from django.db import migrations


def get_name(category_and_name):
    ss = category_and_name.split(':', 1)
    if len(ss) == 2:
        return ss[0], ss[1]
    else:
        return '_default', ss[0]


def delete_external_links(apps, schema_editor):
    Article = apps.get_model("web", "Article")
    ExternalLink = apps.get_model("web", "ExternalLink")
    db = schema_editor.connection.alias
    first_log = False
    # not optimal. easiest, because of name shenanigans we can't easily do join
    for link in ExternalLink.objects.using(db).all().distinct('link_from'):
        category, name = get_name(link.link_from)
        if not len(Article.objects.filter(category__iexact=category, name__iexact=name)):
            if not first_log:
                print('\n', end='')
                first_log = True
            print('    delete: %s\n    ' % (link.link_from), end='')
            sys.stdout.flush()
            ExternalLink.objects.using(db).filter(link_from__iexact=link.link_from).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0014_rename_external_links'),
    ]

    operations = [
        migrations.RunPython(delete_external_links)
    ]
