from django.db import migrations


def add_default(apps, schema_editor):
    Site = apps.get_model("web", "Site")
    TagsCategory = apps.get_model("web", "TagsCategory")
    Tag = apps.get_model("web", "Tag")
    for site in Site.objects.all():
        category, _ = TagsCategory.objects.get_or_create(slug="_default", site=site)
        for tag in Tag.objects.filter(site=site):
            if not tag.category:
                tag.category = category
                tag.save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0028_alter_article_options_alter_articlelogentry_options_and_more'),
    ]

    operations = [
        migrations.RunPython(add_default, atomic=True)
    ]