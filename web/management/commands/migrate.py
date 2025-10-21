from django.core.management.commands.migrate import Command as MigrateCommand

from web.signals import just_after_migration


class Command(MigrateCommand):
    def migration_progress_callback(self, action, migration=None, fake=False):
        super().migration_progress_callback(action, migration, fake)
        just_after_migration.send(
            sender=self,
            migration=f'{migration.app_label}.{migration.name[:migration.name.index('_')]}' if migration else None,
            action=action
        )