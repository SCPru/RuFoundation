from django.http import HttpRequest, HttpResponse
from django.conf import settings

from . import APIView, render_error, render_json

from web.controllers import articles

from typing import Optional
import json


def _validate_article_data(data, allow_partial=False) -> Optional[HttpResponse]:
    if 'pageId' not in data or not data['pageId'] or not articles.is_full_name_allowed(data['pageId']):
        return render_error(400, 'Некорректный ID страницы')
    if ('source' not in data or not (data['source'] or '').strip()) and not (allow_partial and 'source' not in data):
        return render_error(400, 'Отсутствует исходный код страницы')
    if ('title' not in data or not (data['title'] or '').strip()) and not (allow_partial and 'title' not in data):
        return render_error(400, 'Отсутствует название страницы')
    return None


class CreateView(APIView):
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not settings.ANONYMOUS_EDITING_ENABLED and not request.user.has_perm("web.create_article"):
            return render_error(403, "Недостаточно прав")

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


class FetchOrUpdateView(APIView):
    def get(self, request: HttpRequest, full_name: str) -> HttpResponse:
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

    def put(self, request: HttpRequest, full_name: str) -> HttpResponse:
        # find page
        article = articles.get_article(full_name)
        if article is None:
            return render_error(404, 'Страница не найдена')

        if not settings.ANONYMOUS_EDITING_ENABLED and not request.user.has_perm("web.edit_article", article):
            return render_error(403, 'Недостаточно прав')

        data = json.loads(request.body.decode('utf-8'))

        err = _validate_article_data(data, allow_partial=True)
        if err is not None:
            return err

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


class FetchLogView(APIView):
    def get(self, request: HttpRequest, full_name: str) -> HttpResponse:
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
