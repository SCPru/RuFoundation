from django.conf import settings
from django.db import models
from django.db.models import Func, Value
from django.db.models.lookups import Exact

from .articles import Article
from .sites import SiteLimitedModel


class ForumSection(SiteLimitedModel):
    class Meta:
        verbose_name = "Категория форума"
        verbose_name_plural = "Категории форума"

    name = models.TextField(verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    order = models.IntegerField(verbose_name="Порядок сортировки", default=0, blank=True)
    # this is hidden for anyone unless they click "show hidden"
    is_hidden = models.BooleanField(verbose_name="Скрытая категория", default=False)
    # this is displayed for moderators and admins but completely hidden for users
    is_hidden_for_users = models.BooleanField(verbose_name="Видима только модераторам", default=False)

    def __str__(self):
        return self.name


class ForumCategory(SiteLimitedModel):
    class Meta:
        verbose_name = "Раздел форума"
        verbose_name_plural = "Разделы форума"

    name = models.TextField(verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    order = models.IntegerField(verbose_name="Порядок сортировки", default=0, blank=True)
    section = models.ForeignKey(to=ForumSection, on_delete=models.DO_NOTHING, verbose_name="Категория")  # to-do: review later
    is_for_comments = models.BooleanField(verbose_name="Отображать комментарии к статьям в этом разделе", default=False)

    def __str__(self):
        return self.name


class ForumThread(SiteLimitedModel):
    class Meta:
        verbose_name = "Тема форума"
        verbose_name_plural = "Темы форума"

        constraints = [
            # logic: a thread must have either 'article' or 'category' assigned
            # requires postgres >9.2
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_category_or_article',
                check=Exact(
                    lhs=Func('article_id', 'category_id', function='num_nonnulls', output_field=models.IntegerField()),
                    rhs=Value(1),
                ),
            )
        ]

    name = models.TextField(verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    category = models.ForeignKey(to=ForumCategory, on_delete=models.DO_NOTHING, null=True, verbose_name="Раздел (если это тема)")  # to-do: review later
    article = models.ForeignKey(to=Article, on_delete=models.CASCADE, null=True, verbose_name="Статья (если это комментарии)")
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Автор")


class ForumPost(SiteLimitedModel):
    class Meta:
        verbose_name = "Сообщение форума"
        verbose_name_plural = "Сообщения форума"

    name = models.TextField(verbose_name="Название", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время изменения")
    deleted_at = models.DateTimeField(verbose_name="Время удаления")
    author = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    reply_to = models.ForeignKey(to='ForumPost', on_delete=models.SET_NULL, null=True, verbose_name="Ответ на комментарий")
    thread = models.ForeignKey(to=ForumThread, on_delete=models.CASCADE, verbose_name="Тема")


class ForumPostVersion(SiteLimitedModel):
    class Meta:
        verbose_name = "Версия сообщения форума"
        verbose_name_plural = "Версии сообщений форума"

    post = models.ForeignKey(to=ForumPost, on_delete=models.CASCADE, verbose_name="Сообщение")
    source = models.TextField(verbose_name="Текст сообщения")
