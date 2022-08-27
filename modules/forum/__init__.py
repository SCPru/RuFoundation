from modules import ModuleError
from renderer import RenderContext, render_template_from_string
from renderer.templates import apply_template

import renderer
import re

from web.controllers import articles
from web.models.forum import ForumCategory, ForumThread, ForumSection, ForumPost


def has_content():
    return False


def render_thread(context: RenderContext, params, thread):
    return 'thread view is not supported yet'


def render_category(context: RenderContext, params, category):
    return 'category view is not supported yet'


def render_start(context: RenderContext, params):
    context.title = 'Разделы форума'

    categories = ForumCategory.objects.all().order_by('order')
    sections = ForumSection.objects.all().order_by('order')

    items = []
    for section in sections:
        item = {'name': section.name, 'description': section.description, 'categories': []}
        for category in categories:
            if category.section_id != section.id:
                continue
            citem = {
                'name': category.name,
                'description': category.description,
                'url': '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name))
            }
            if category.is_for_comments:
                citem['threads'] = ForumThread.objects.filter(article_id__isnull=False).count()
                citem['posts'] = ForumPost.objects.filter(thread__article_id__isnull=False).count()
            else:
                citem['threads'] = ForumThread.objects.filter(category=category).count()
                citem['posts'] = ForumPost.objects.filter(thread__category=category).count()
            item['categories'].append(citem)
        items.append(item)

    return render_template_from_string(
        """
        <div class="forum-start-box">
        {% for section in sections %}
            <div class="forum-group">
                <div class="head">
                    <div class="title">{{ section.name }}</div>
                    <div class="description">{{ section.description }}</div>
                </div>
                <div>
                    <table>
                    <tbody>
                    <tr class="head">
                        <td>Название категории</td>
                        <td>Темы</td>
                        <td>Сообщения</td>
                        <td>Последнее сообщение</td>
                    </tr>
                    {% for category in section.categories %}
                        <tr>
                            <td class="name">
                                <div class="title"><a href="{{ category.url }}">{{ category.name }}</a></div>
                                <div class="description">{{ category.description }}</div>
                            </td>
                            <td class="threads">{{ category.threads }}</td>
                            <td class="posts">{{ category.posts }}</td>
                            <td class="last"></td>
                        </tr>
                    {% endfor %}
                    </tbody>
                    </table>
                </div>
            </div>
        {% endfor %}
        </div>
        """,
        sections=items
    )


def render(context: RenderContext, params):
    context.title = 'Форум'

    category = None
    thread = None

    for param in context.path_params:
        if param.startswith('c-'):
            try:
                category = int(param[2:])
            except ValueError:
                category = param[2:]
        elif param.startswith('t-'):
            try:
                thread = int(param[2:])
            except ValueError:
                thread = param[2:]

    if category is not None:
        c = ForumCategory.objects.filter(id=category)
        if not c:
            context.status = 404
            raise ModuleError('Категория "%s" не найдена' % category)
        return render_category(context, params, c[0])

    if thread is not None:
        t = ForumThread.objects.filter(id=thread)
        if not t:
            context.status = 404
            raise ModuleError('Тема "%s" не найдена' % thread)
        return render_thread(context, params, t[0])

    return render_start(context, params)