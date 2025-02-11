from django.core.management.base import BaseCommand, CommandError

from web import seeds, threadvars
from web.models.site import Site


class Command(BaseCommand):
    help = 'Seeds the database'

    def add_arguments(self, parser):
        parser.add_argument("-a", "--archive", required=False, help="Seeds from specified archive")
        # parser.add_argument("-o", "--fetch-from", required=False, help="Fetch from existing site, running on RuFoundation Engine.\nMake sure that the site engine version matches your version")
        parser.add_argument("-f", "--forum", required=False, action='store_true', help="Seeds the forum (only applicable for Archive)")

    def handle(self, *args, **options):
        if not Site.objects.exists():
            raise CommandError("You must create new site to run this command")

        site = Site.objects.get()
        
        with threadvars.context():
            threadvars.put('current_site', site)
            if options["archive"]:
                if not options["forum"]:
                    from web.seeds import from_archive
                    from_archive.run(options["archive"])
                else:
                    from web.seeds import forum_from_archive
                    forum_from_archive.run(options["archive"])
            else:
                seeds.run()
