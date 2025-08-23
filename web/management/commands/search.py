from django.core.management.base import BaseCommand
from web.controllers.search import search_articles


class Command(BaseCommand):
    help = 'Searches for article'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--text', required=True, help='Text to search')
        parser.add_argument('-s', '--source', required=False, action='store_true', help='Search source code')

    def handle(self, *args, **options):
        result = search_articles(options['text'], is_source=options.get('source'))
        print(repr(result))
