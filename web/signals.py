from django.dispatch import Signal


just_after_migration = Signal(['migration', 'action'])
