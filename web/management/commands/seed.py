from django.core.management.base import BaseCommand

from web import seeds, threadvars
from web.models.sites import Site


class Command(BaseCommand):
    help = 'Seeds the database'

    def add_arguments(self, parser):
        parser.add_argument("-a", "--archive", required=False, help="Seeds from specified archive")
        parser.add_argument("-s", "--site-slug", required=True, help="Slug for site that items will be added to")

    def handle(self, *args, **options):
        site = Site.objects.get(slug=options["site_slug"])
        with threadvars.context():
            threadvars.put('current_site', site)
            if options["archive"]:
                from web.seeds import from_archive
                from_archive.run(options["archive"])
            else:
                seeds.run()
