from django.core.management.commands.migrate import Command as MigrateCommand
from django.core.management.base import no_translations
from django.db.migrations.recorder import MigrationRecorder

from web.signals import after_migration

class Command(MigrateCommand):
    @no_translations
    def handle(self, *args, **kwargs):
        migrations_before = {migration.name for migration in MigrationRecorder.Migration.objects.all()}
        result = super().handle(*args, **kwargs)
        migrations_after = {migration.name for migration in MigrationRecorder.Migration.objects.all()}

        current_migrated = migrations_after.difference(migrations_before)

        for migration in current_migrated:
            after_migration(migration[:migration.index('_')])

        return result
