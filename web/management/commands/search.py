from django.core.management.base import BaseCommand
from web.controllers.search import search_articles


class Command(BaseCommand):
    help = 'Searches for article'

    def add_arguments(self, parser):
        parser.add_argument('-t', '--text', required=True, help='Text to search')
        parser.add_argument('-s', '--source', required=False, action='store_true', help='Search source code')
        parser.add_argument('-c', '--cursor', required=False, help='Cursor for pagination')
        parser.add_argument('-l', '--limit', required=False, type=int, default=25, help='Max results')

    def handle(self, *args, **options):
        cursor = options.get('cursor')
        limit = options.get('limit')
        result = search_articles(
            options['text'],
            is_source=options.get('source'),
            cursor=cursor,
            limit=limit,
            explain=True
        )
        print(repr(result))
