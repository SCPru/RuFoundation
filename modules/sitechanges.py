import math
import json
import operator

from functools import reduce

from django.db.models import Q

from renderer import RenderContext, render_template_from_string, render_user_to_html

from modules.listpages import render_pagination, render_date

from renderer.utils import render_user_to_text
from web.models.users import User
from web.models.articles import ArticleLogEntry, Article
from web.models.settings import Settings
from web.controllers import articles


def has_content():
    return False


def log_entry_type_name(entry: ArticleLogEntry.LogEntryType) -> tuple[str, str]:
    mapping = {
        ArticleLogEntry.LogEntryType.Source: ('S', 'изменился текст статьи'),
        ArticleLogEntry.LogEntryType.Title: ('T', 'изменился заголовок'),
        ArticleLogEntry.LogEntryType.Name: ('R', 'страница переименована/удалена'),
        ArticleLogEntry.LogEntryType.Tags: ('A', 'метки изменились'),
        ArticleLogEntry.LogEntryType.New: ('N', 'создана новая страница'),
        ArticleLogEntry.LogEntryType.Parent: ('M', 'изменилась родительская страница'),
        ArticleLogEntry.LogEntryType.FileAdded: ('F', 'файл добавлен'),
        ArticleLogEntry.LogEntryType.FileDeleted: ('F', 'файл удалён'),
        ArticleLogEntry.LogEntryType.FileRenamed: ('F', 'файл переименован'),
        ArticleLogEntry.LogEntryType.VotesDeleted: ('V', 'голоса изменены'),
        ArticleLogEntry.LogEntryType.Authorship: ('C', 'авторство изменено'),
        ArticleLogEntry.LogEntryType.Wikidot: ('W', 'правка, портированная с Wikidot')
    }
    return mapping.get(entry, ('?', '?'))


def log_entry_default_comment(entry: ArticleLogEntry) -> str:
    if entry.comment.strip():
        return entry.comment

    if entry.type == ArticleLogEntry.LogEntryType.New:
        return 'Создание новой страницы'

    if entry.type == ArticleLogEntry.LogEntryType.Title:
        return f'Заголовок изменён с "{entry.meta['prev_title']}" на "{entry.meta['title']}"'

    if entry.type == ArticleLogEntry.LogEntryType.Name:
        return f'Страница переименована из "{entry.meta['prev_name']}" в "{entry.meta['name']}"'

    if entry.type == ArticleLogEntry.LogEntryType.Tags:
        added_tags = [x['name'] for x in entry.meta.get('added_tags', [])]
        removed_tags = [x['name'] for x in entry.meta.get('removed_tags', [])]
        log = [
            added_tags and f'Добавлены теги: {', '.join(added_tags)}.',
            removed_tags and f'Удалены теги: {', '.join(removed_tags)}.'
        ]
        return ' '.join(l for l in log if l)

    if entry.type == ArticleLogEntry.LogEntryType.Parent:
        if entry.meta['prev_parent'] and entry.meta['parent']:
            return f'Родительская страница изменена с "{entry.meta['prev_parent']}" на "{entry.meta['parent']}"'
        if entry.meta['prev_parent']:
            return f'Убрана родительская страница "{entry.meta['prev_parent']}"'
        if entry.meta['parent']:
            return f'Установлена родительская страница "{entry.meta['parent']}"'

    if entry.type == ArticleLogEntry.LogEntryType.FileAdded:
        return f'Загружен файл: "{entry.meta['name']}"'

    if entry.type == ArticleLogEntry.LogEntryType.FileDeleted:
        return f'Удалён файл: "{entry.meta['name']}"'

    if entry.type == ArticleLogEntry.LogEntryType.FileRenamed:
        return f'Переименован файл: "{entry.meta['prev_name']}" в "{entry.meta['name']}"'

    if entry.type == ArticleLogEntry.LogEntryType.VotesDeleted:
        rating_str = 'n/a'
        if entry.meta['rating_mode'] == Settings.RatingMode.UpDown:
            rating_str = '%+d' % int(entry.meta['rating'])
        elif entry.meta['rating_mode'] == Settings.RatingMode.Stars:
            rating_str = '%.1f' % float(entry.meta['rating'])
        return f'Сброшен рейтинг страницы: {rating_str} (голосов: {entry.meta['votes_count']}, популярность: {entry.meta['popularity']}%)'
    
    if entry.type == ArticleLogEntry.LogEntryType.Authorship:
        added_authors = User.objects.filter(id__in=entry.meta.get('added_authors', []))
        removed_authors = User.objects.filter(id__in=entry.meta.get('removed_authors', []))
        added_authors = [render_user_to_text(a) for a in added_authors]
        removed_authors = [render_user_to_text(a) for a in removed_authors]
        log = [
            added_authors and f'Добавлены авторы: {', '.join(added_authors)}.',
            removed_authors and f'Удалены авторы: {', '.join(removed_authors)}.'
        ]
        return ' '.join(l for l in log if l)

    if entry.type == ArticleLogEntry.LogEntryType.Revert:
        return f'Откат страницы к версии №{entry.meta['rev_number']}'

    return ''


def render(context: RenderContext, params):
    all_types = [str(x) for x in ArticleLogEntry.LogEntryType]
    filter_types = []
    for param in context.path_params:
        if param in all_types and param not in filter_types and context.path_params[param].lower() == 'true':
            filter_types.append(param)

    try:
        page = int(context.path_params.get('p'))
    except:
        page = 1
    if page < 1:
        page = 1

    per_page = int(context.path_params.get('perpage', '20'))
    category = context.path_params.get('category', '*').lower()
    user_name = context.path_params.get('username', '').lower().strip()

    q = ArticleLogEntry.objects.all()

    hidden_categories = articles.get_hidden_categories_for(context.user)
    q = q.exclude(article__category__in=hidden_categories)

    if filter_types:
        q = q.filter(Q(type__in=filter_types) | reduce(operator.or_, (Q(meta__subtypes__contains=x) for x in filter_types)))

    if category != '*':
        q = q.filter(article__category=category)

    user_name_partial = False
    user_name_search = user_name
    if user_name.startswith('~'):
        user_name_partial = True
        user_name_search = user_name[1:].strip()

    if user_name_search:
        if user_name_partial:
            user_q = list(User.objects.filter(Q(username__icontains=user_name_search)|Q(wikidot_username__icontains=user_name_search)))
            new_q = Q(user__in=user_q)
            if user_name_search in 'system':
                new_q |= Q(user__isnull=True)
        else:
            user_q = list(User.objects.filter(Q(username=user_name_search)|Q(wikidot_username=user_name_search)))
            new_q = Q(user__in=user_q)
            if user_name_search == 'system':
                new_q |= Q(user__isnull=True)
        q = q.filter(new_q)

    q = q.order_by('-created_at')

    total = q.count()

    max_page = max(1, int(math.ceil(total / per_page)))
    if page > max_page:
        page = max_page

    raw_entries = q[(page - 1) * per_page:page * per_page]
    entries = []
    for entry in raw_entries:
        types = []
        if 'subtypes' in entry.meta:
            for subtype in entry.meta['subtypes']:
                t, desc = log_entry_type_name(subtype)
                types.append({'id': t, 'desc': desc})
        else:
            t, desc = log_entry_type_name(entry.type)
            types.append({'id': t, 'desc': desc})
        entries.append({
            'rev_number': entry.rev_number,
            'types': types,
            'comment': log_entry_default_comment(entry),
            'author': render_user_to_html(entry.user),
            'date': render_date(entry.created_at),
            'article_title': entry.article.title,
            'article_category': entry.article.category,
            'article_url': '/%s' % entry.article.full_name
        })

    categories = sorted(Article.objects.distinct('category').exclude(category__in=hidden_categories).values_list('category', flat=True))

    type_filter = []
    type_filter_empty = not filter_types
    for t in all_types:
        if t == ArticleLogEntry.LogEntryType.Revert:
            continue
        desc = log_entry_type_name(ArticleLogEntry.LogEntryType(t))[1]
        type_filter.append({
            'name': desc,
            'id': t,
            'selected': t in filter_types
        })

    return render_template_from_string(
        """
        <div class="site-changes-box w-site-changes" data-site-changes-path-params="{{ data_path_params }}" data-site-changes-params="{{ data_params }}">
            <style>
                .changes-list{}
                
                .changes-list .pager{
                    margin: 1em 0;
                    text-align: center;
                }
                
                .changes-list-item{
                    /* overflow: hidden; */
                    padding: 2px;
                }
                
                .changes-list-item:hover{
                    background-color: #F2F2F2;
                }
                
                .changes-list-item table{
                    width: 98%;
                    
                }
                
                .changes-list-item .title{
                
                }
                
                .changes-list-item .mod-date{
                    text-align: right;
                    width: 13em;
                
                }
                .changes-list-item .revision-no{
                    text-align: center;
                    width: 7em;
                }
                .changes-list-item .flags{
                    text-align: left;
                    width: 3em;
                }
                .changes-list-item .mod-by{
                    width: 15em;
                    text-align: left;
                }
                
                .changes-list-item .comments{
                    font-size: 95%;
                    color: #666;
                    margin: 2px 0;
                }
            </style>
            <form onsubmit="return false;" action="" method="get">
                <table class="form">
                <tbody>
                <tr>
                    <td>Типы правок:</td>
                    <td class="w-type-filter">
                        <label>
                            <input type="checkbox" class="checkbox"{%if type_filter_empty%} checked{%endif%} name="*">
                            ВСЕ
                        </label>
                        <br>
                        {% for f in type_filter %}
                            <label>
                                <input type="checkbox" class="checkbox"{%if f.selected%} checked{%endif%} name="{{ f.id }}">
                                {{ f.name }}
                            </label>
                            <br>
                        {% endfor %}
                    </td>
                </tr>
                <tr>
                    <td>Из категории:</td>
                    <td>
                        <select id="rev-category">
                            <option value="*"{% if category_param == '*' %} selected{% endif %}>Все категории</option>
                            {% for category in categories %}
                                <option value="{{ category }}"{% if category == category_param %} selected{% endif %}>
                                    {{ category }}
                                </option>
                            {% endfor %}
                        </select>
                    </td>
                </tr>
                <tr>
                    <td>Фильтр по имени пользователя:<br><span style="font-size: 75%">Используйте префикс "~" для фильтрации<br>по частичному имени пользователя</span></td>
                    <td>
                        <input value="{{ user_name }}" id="rev-username"> 
                    </td>
                </tr>
                <tr>
                    <td>Правок на страницу:</td>
                    <td>
                        <select id="rev-perpage">
                            <option value="10"{%if per_page == 10%} selected{%endif%}>10</option>
                            <option value="20"{%if per_page == 20%} selected{%endif%}>20</option>
                            <option value="50"{%if per_page == 50%} selected{%endif%}>50</option>
                            <option value="100"{%if per_page == 100%} selected{%endif%}>100</option>
                            <option value="200"{%if per_page == 200%} selected{%endif%}>200</option>
                        </select>
                    </td>
                </tr>
                </tbody>
                </table>
                <div class="buttons">
                    <input class="btn btn-default btn-sm" type="button" value="Обновить список">
                </div>
            </form>
            <div id="site-changes-list" class="changes-list">
                {{ pagination }}
                {% for entry in entries %}
                <div class="changes-list-item">
                    <table>
                    <tbody>
                    <tr>
                        <td class="title">
                            <a href="{{ entry.article_url }}">
                                {% if entry.article_category != '_default' %}
                                    {{ entry.article_category }}:
                                {% endif %}
                                {{ entry.article_title }}
                            </a>
                        </td>
                        <td class="flags">
                            {% for t in entry.types %}<span class="spantip" title="{{ t.desc }}">{{ t.id }}</span>{% endfor %}
                        </td>
                        <td class="mod-date">
                            {{ entry.date }}
                        </td>
                        <td class="revision-no">
                            (рев. {{ entry.rev_number }}) 
                        </td>
                        <td class="mod-by">
                            {{ entry.author }}
                        </td>
                    </tr>
                    </tbody>
                    </table>
                    {% if entry.comment %}
                        <div class="comments">
                            {{ entry.comment }}
                        </div>
                    {% endif %}
                </div>
                {% endfor %}
                {{ pagination }}
            </div>
        </div>
        """,
        entries=entries,
        categories=categories,
        pagination=render_pagination(None, page, max_page) if max_page != 1 else '',
        data_path_params=json.dumps(context.path_params),
        data_params=json.dumps(params),
        category_param=category,
        user_name=user_name,
        type_filter=type_filter,
        type_filter_empty=type_filter_empty,
        per_page=per_page
    )
