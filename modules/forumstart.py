from modules import ModuleError
from renderer import RenderContext, render_template_from_string
from web.controllers import articles, permissions
from web.models.forum import ForumCategory, ForumThread, ForumSection, ForumPost


def has_content():
    return False


def render(context: RenderContext, params):
    context.title = 'Разделы форума'

    hidden = context.path_params.get('hidden', 'hide')

    categories = ForumCategory.objects.all().order_by('order')
    sections = ForumSection.objects.all().order_by('order')

    if hidden != 'show':
        sections = sections.filter(is_hidden=False)

    items = []
    for section in sections:
        if not permissions.check(context.user, 'view', section):
            continue
        item = {'name': section.name, 'description': section.description, 'categories': []}
        for category in categories:
            if category.section_id != section.id:
                continue
            if not permissions.check(context.user, 'view', category):
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
        if item['categories']:
            items.append(item)

    return render_template_from_string(
        """
        <div class="forum-start-box">
        {% for section in sections %}
            <div class="forum-group" style="width: 98%">
                <div class="head">
                    <div class="title">{{ section.name }}</div>
                    <div class="description">{{ section.description }}</div>
                </div>
                <div>
                    <table>
                    <tbody>
                    <tr class="head">
                        <td>Название категории</td>
                        <td>Тем</td>
                        <td>Сообщений</td>
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
        <p style="text-align: right">
            {% if hidden == 'show' %}
                <a href="/forum/start">Скрыть скрытые</a>
            {% else %}
                <a href="/forum/start/hidden/show">Показать скрытые</a>
            {% endif %}
        </p>
        """,
        sections=items,
        hidden=hidden
    )
