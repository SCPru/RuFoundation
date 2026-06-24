from dynamic_preferences.types import BooleanPreference, ChoicePreference
from dynamic_preferences.preferences import Section
from dynamic_preferences.users.registries import user_preferences_registry


articles = Section('qol', 'Удобство')

@user_preferences_registry.register
class AdvancedSourceEditorEnabled(BooleanPreference):
    section = articles
    name = 'advanced_source_editor_enabled'
    verbose_name = 'Расширенный редактор исходного кода'
    default = False


@user_preferences_registry.register
class ForumDisplayMode(ChoicePreference):
    section = articles
    name = 'forum_display_mode'
    verbose_name = 'Режим просмотра форума'
    default = 'pagination'
    choices = (
        ('pagination', 'Пагинация'),
        ('infinite', 'Бесконечная прокрутка'),
    )


@user_preferences_registry.register
class ForumSortOrder(ChoicePreference):
    section = articles
    name = 'forum_sort_order'
    verbose_name = 'Порядок сообщений форума'
    default = 'oldest'
    choices = (
        ('oldest', 'Старые сверху'),
        ('newest', 'Новые сверху'),
    )
