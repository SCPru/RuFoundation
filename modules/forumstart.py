from modules import ModuleError
from modules.listpages import render_date
from renderer import RenderContext, render_template_from_string, render_user_to_html
from web.controllers import articles, permissions
from web.models.forum import ForumCategory, ForumThread, ForumSection, ForumPost


def has_content():
    return False


def render(context: RenderContext, params):
    context.title = 'Разделы форума'

    hidden = context.path_params.get('hidden', 'hide')

    categories = ForumCategory.objects.all().order_by('order', 'id')
    sections = ForumSection.objects.all().order_by('order', 'id')

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
                last_post = ForumPost.objects.filter(thread__article_id__isnull=False).order_by('-created_at')[:1]
            else:
                citem['threads'] = ForumThread.objects.filter(category=category).count()
                citem['posts'] = ForumPost.objects.filter(thread__category=category).count()
                last_post = ForumPost.objects.filter(thread__category=category).order_by('-created_at')[:1]
            if last_post:
                last_post = last_post[0]
                citem['last_post_date'] = render_date(last_post.created_at)
                citem['last_post_url'] = '/forum/t-%d/%s#post-%d' % (last_post.thread.id, articles.normalize_article_name(last_post.thread.name if last_post.thread.category_id else last_post.thread.article.display_name), last_post.id)
                citem['last_post_user'] = render_user_to_html(last_post.author)
            else:
                citem['last_post_date'] = None
                citem['last_post_url'] = None
                citem['last_post_user'] = None
            print(repr(citem))
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
                            <td class="last">
                                {% if category.last_post_url %}
                                    Автор: {{ category.last_post_user }}
                                    <br>
                                    {{ category.last_post_date }}
                                    <br>
                                    <a href="{{ category.last_post_url }}">Перейти</a>
                                {% endif %}
                            </td>
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
