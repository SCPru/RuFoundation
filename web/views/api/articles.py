import json
from django.conf import settings

from . import render_error, render_json, restrict_method

from web.controllers import articles


def _validate_article_data(data, allow_partial=False):
    if 'pageId' not in data or not data['pageId'] or not articles.is_full_name_allowed(data['pageId']):
        return render_error(400, 'Некорректный ID страницы')
    if ('source' not in data or not (data['source'] or '').strip()) and not (allow_partial and 'source' not in data):
        return render_error(400, 'Отсутствует исходный код страницы')
    if ('title' not in data or not (data['title'] or '').strip()) and not (allow_partial and 'title' not in data):
        return render_error(400, 'Отсутствует название страницы')
    return None


@restrict_method('POST')
def create(request):
    if not settings.ANONYMOUS_EDITING_ENABLED:
        return render_error(403, 'Недостаточно прав')
    data = json.loads(request.body.decode('utf-8'))
    err = _validate_article_data(data)
    if err is not None:
        return err
    article = articles.get_article(data['pageId'])
    if article is not None:
        return render_error(409, 'Страница с таким ID уже существует')
    # create page
    article = articles.create_article(data['pageId'])
    article.title = data['title']
    article.save()
    articles.create_article_version(article, data['source'])
    return render_json(201, {'status': 'ok'})


@restrict_method('GET', 'PUT')
def fetch_or_update(request, full_name):
    if request.method == 'GET':
        return fetch(request, full_name)
    elif request.method == 'PUT':
        return update(request, full_name)


def fetch(request, full_name):
    # find page
    article = articles.get_article(full_name)
    if article is None:
        return render_error(404, 'Страница не найдена')
    # latest source
    source = articles.get_latest_source(article)
    return render_json(200, {
        'pageId': full_name,
        'title': article.title,
        'source': source
    })


def update(request, full_name):
    if not settings.ANONYMOUS_EDITING_ENABLED:
        return render_error(403, 'Недостаточно прав')
    data = json.loads(request.body.decode('utf-8'))
    err = _validate_article_data(data, allow_partial=True)
    if err is not None:
        return err
    # find page
    article = articles.get_article(full_name)
    if article is None:
        return render_error(404, 'Страница не найдена')
    # check if renaming
    if data['pageId'] != full_name:
        article2 = articles.get_article(data['pageId'])
        if article2 is not None:
            return render_error(409, 'Страница с таким ID уже существует')
        articles.update_full_name(article, data['pageId'])
    # check if changing title
    if 'title' in data and data['title'] != article.title:
        articles.update_title(article, data['title'])
    # check if changing source
    if 'source' in data and data['source'] != articles.get_latest_source(article):
        articles.create_article_version(article, data['source'])
    return render_json(200, {'status': 'ok'})


@restrict_method('GET')
def fetch_log(request, full_name):
    try:
        c_from = int(request.GET.get('from', '0'))
        c_to = int(request.GET.get('to', '25'))
    except ValueError:
        return render_error(400, 'Некорректное указание ограничений списка')
    log_entries, total_count = articles.get_log_entries_paged(full_name, c_from, c_to)
    output = []
    for entry in log_entries:
        output.append({
            'revNumber': entry.rev_number,
            'comment': entry.comment,
            'createdAt': entry.created_at.isoformat(),
            'type': entry.type,
            'meta': entry.meta
        })
    return render_json(200, {'count': total_count, 'entries': output})
