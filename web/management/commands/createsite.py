from django.core.management.base import BaseCommand

from web.models.settings import Settings
from web.models.sites import Site


class Command(BaseCommand):
    help = 'Creates a website'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--slug', required=True, help='Slug of the website (e.g.: scp-ru, scp, wl)')
        parser.add_argument('-d', '--domain', required=True, help='Domain of the website (e.g.: scpfoundation.net)')
        parser.add_argument('-D', '--media-domain', required=False, help='Isolated local-files domain (e.g.: files.scpfoundation.net)')
        parser.add_argument('-t', '--title', required=True, help='Name of the website (e.g.: SCP Foundation)')
        parser.add_argument('-H', '--headline', required=True, help='Headline of the website (e.g.: Secure, Contain, Protect)')

    def handle(self, *args, **options):
        media_domain = options["media_domain"] if options["media_domain"] else options["domain"]

        site = Site(
            title=options["title"],
            headline=options["headline"],
            slug=options["slug"],
            domain=options["domain"],
            media_domain=media_domain
        )
        site.save()

        settings = Settings(site=site)
        settings.save()
