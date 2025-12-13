from dynamic_preferences.types import BooleanPreference
from dynamic_preferences.preferences import Section
from dynamic_preferences.users.registries import user_preferences_registry


articles = Section('qol')

@user_preferences_registry.register
class AdvancedSourceEditorEnabled(BooleanPreference):
    section = articles
    name = 'advanced_source_editor_enabled'
    default = False