from web.controllers.articles import get_latest_log_entry
from django.db import migrations


def update_updated_at(apps, schema_editor):
    Site = apps.get_model("web", "Site")
    Article = apps.get_model("web", "Article")
    ArticleLogEntry = apps.get_model("web", "ArticleLogEntry")
    for site in Site.objects.all():
        articles = Article.objects.filter(site=site)
        for article in articles:
            latest = ArticleLogEntry.objects.filter(article=article).order_by('-rev_number').first()
            if latest and article.updated_at != latest.created_at:
                article.updated_at = latest.created_at
                article.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0029_add_default_category'),
    ]

    operations = [
        migrations.RunPython(update_updated_at, reverse_func, atomic=True)
    ]