import json

from . import render_error, render_json

from web.controllers import articles


def create(request):
    if request.method != 'POST':
        return render_error(405, 'Некорректный метод запроса')
    data = json.loads(request.body.decode('utf-8'))
    if 'pageId' not in data or not data['pageId'] or not articles.is_full_name_allowed(data['pageId']):
        return render_error(400, 'Некорректный ID страницы')
    if 'source' not in data or not data['source']:
        return render_error(400, 'Исходный код страницы отсутствует')
    article = articles.get_article(data['pageId'])
    if article is not None:
        return render_error(409, 'Страница с таким ID уже существует')
    # create page
    article = articles.create_article(data['pageId'])
    articles.create_article_version(article, data['source'])
    return render_json(201, {'status': 'ok'})
