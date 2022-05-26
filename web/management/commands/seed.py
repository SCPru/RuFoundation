from django.core.management.base import BaseCommand

from web import seeds


class Command(BaseCommand):
    help = 'Seeding the database'

    def add_arguments(self, parser):
        parser.add_argument("-a", "--archive", required=False, help="Seeding from specified archive")

    def handle(self, *args, **options):
        if options["archive"]:
            from web.seeds import from_archive
            from_archive.run(options["archive"])
        seeds.run()
