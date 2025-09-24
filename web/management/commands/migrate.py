from django.core.management.commands.migrate import Command as MigrateCommand
from django.core.management.base import no_translations
from django.db.migrations.executor import MigrationExecutor
from django.db import connections

from web.signals import after_migration, after_migration_jit


class Command(MigrateCommand):
    @no_translations
    def handle(self, *args, **kwargs):
        database = kwargs["database"]

        connection = connections[database]
        connection.prepare_database()

        executor = MigrationExecutor(connection, self.migration_progress_callback)
        executor.loader.check_consistent_history(connection)

        migrations_before = set(executor.loader.applied_migrations)
        result = super().handle(*args, **kwargs)
        migrations_after = set(executor.loader.applied_migrations)

        current_migrated = migrations_after.difference(migrations_before)

        for migration in current_migrated:
            after_migration(migration[:migration.index('_')])

        return result
    
    def migration_progress_callback(self, action, migration=None, fake=False):
        super().migration_progress_callback(action, migration, fake)
        if action == 'apply_success':
            after_migration_jit(migration.name[:migration.name.index('_')])
