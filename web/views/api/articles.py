import json

from . import render_error, render_json

from web.controllers import articles


def _validate_article_data(data):
    if 'pageId' not in data or not data['pageId'] or not articles.is_full_name_allowed(data['pageId']):
        return render_error(400, 'Некорректный ID страницы')
    if 'source' not in data or not (data['source'] or '').strip():
        return render_error(400, 'Отсутствует исходный код страницы')
    if 'title' not in data or not (data['title'] or '').strip():
        return render_error(400, 'Отсутствует название страницы')
    return None


def create(request):
    if request.method != 'POST':
        return render_error(405, 'Некорректный метод запроса')
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


def fetch_or_update(request, full_name):
    if request.method == 'GET':
        return fetch(request, full_name)
    elif request.method == 'PUT':
        return update(request, full_name)
    else:
        return render_error(405, 'Некорректный метод запроса')


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
    data = json.loads(request.body.decode('utf-8'))
    err = _validate_article_data(data)
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
    if data['title'] != article.title:
        articles.update_title(article, data['title'])
    # check if changing source
    source = articles.get_latest_source(article)
    if data['source'] != source:
        articles.create_article_version(article, data['source'])
    return render_json(200, {'status': 'ok'})
