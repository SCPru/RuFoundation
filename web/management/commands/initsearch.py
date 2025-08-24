import concurrent

from django.core.management.base import BaseCommand
from tqdm import tqdm

from web import threadvars
from web.controllers.search import update_search_index
from web.models import Article, Site


class Command(BaseCommand):
    help = 'Recreates index for article text search.\nNote: very heavy operation.\nUsually done after bulk import or migrating the database.\nPer-article indexes will be updated on-demand and do not require running this'

    def handle(self, *args, **options):
        all_articles = Article.objects.all()

        if not all_articles:
            return

        site = Site.objects.get()

        def worker(article):
            with threadvars.context():
                threadvars.put('current_site', site)
                update_search_index(article)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            list(tqdm(executor.map(worker, all_articles), total=len(all_articles)))
