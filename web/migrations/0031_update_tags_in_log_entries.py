from web.controllers.articles import get_latest_log_entry
from django.db import migrations


get_full_name = lambda tag: f"{tag.category.slug}:{tag.name}" if tag.category.slug == "_default" else tag.name


def update_entries(apps, schema_editor):
    Site = apps.get_model("web", "Site")
    Tag = apps.get_model("web", "Tag")
    ArticleLogEntry = apps.get_model("web", "ArticleLogEntry")
    for site in Site.objects.all():
        for entry in ArticleLogEntry.objects.filter(site=site, type='tags'):
            new_added = []
            new_removed = []
            if 'added_tags' in entry.meta:
                for tag in entry.meta['added_tags']:
                    try:
                        new_tag = Tag.objects.get(site=site, name=tag)
                        new_added.append({'id': new_tag.id, 'name': get_full_name(new_tag)})
                    except Tag.DoesNotExist:
                        pass
                entry.meta['added_tags'] = new_added
            if 'removed_tags' in entry.meta:
                for tag in entry.meta['removed_tags']:
                    try:
                        new_tag = Tag.objects.get(site=site, name=tag)
                        new_removed.append({'id': new_tag.id, 'name': get_full_name(new_tag)})
                    except Tag.DoesNotExist:
                        pass
                entry.meta['removed_tags'] = new_removed
            entry.save()


def reverse_func(apps, schema_editor):
    Site = apps.get_model("web", "Site")
    Tag = apps.get_model("web", "Tag")
    ArticleLogEntry = apps.get_model("web", "ArticleLogEntry")
    for site in Site.objects.all():
        for entry in ArticleLogEntry.objects.filter(site=site, type='tags'):
            new_added = []
            new_removed = []
            if 'added_tags' in entry.meta:
                for tag in entry.meta['added_tags']:
                    try:
                        new_added.append(get_full_name(Tag.objects.get(site=site, id=tag)))
                    except Tag.DoesNotExist:
                        pass
                entry.meta['added_tags'] = new_added
            if 'removed_tags' in entry.meta:
                for tag in entry.meta['removed_tags']:
                    try:
                        new_removed.append(get_full_name(Tag.objects.get(site=site, id=tag)))
                    except Tag.DoesNotExist:
                        pass
                entry.meta['removed_tags'] = new_removed
            entry.save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0030_update_updated_at_to_last_revision'),
    ]

    operations = [
        migrations.RunPython(update_entries, reverse_func, atomic=True)
    ]
