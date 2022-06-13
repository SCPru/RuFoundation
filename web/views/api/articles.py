from django.http import HttpRequest, HttpResponse
from django.conf import settings

from . import APIView, APIError, takes_json

from web.controllers import articles

from renderer.utils import render_user_to_json


class ArticleView(APIView):
    def _validate_article_data(self, data, allow_partial=False):
        if not data:
            raise APIError('Некорректный запрос', 400)
        if 'pageId' not in data or not data['pageId'] or not articles.is_full_name_allowed(data['pageId']):
            raise APIError('Некорректный ID страницы', 400)
        if ('source' not in data or not (data['source'] or '').strip()) and not (
                allow_partial and 'source' not in data):
            raise APIError('Отсутствует исходный код страницы', 400)
        if ('title' not in data or data['title'] is None) and not (allow_partial and 'title' not in data):
            raise APIError('Отсутствует название страницы', 400)


class CreateView(ArticleView):
    @takes_json
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        data = self.json_input

        self._validate_article_data(data)

        category = articles.get_article(data['pageId'])

        if not settings.ANONYMOUS_EDITING_ENABLED and (not articles.has_perm(request.user, "web.add_article")
                                                       or not request.user.has_perm("web.add_article_in_category",
                                                                                    category)):
            raise APIError('Недостаточно прав', 403)

        article = articles.get_article(data['pageId'])
        if article is not None:
            raise APIError('Страница с таким ID уже существует', 409)

        # create page
        article = articles.create_article(data['pageId'])
        article.title = data['title']
        article.save()
        articles.create_article_version(article, data['source'], request.user)

        return self.render_json(201, {'status': 'ok'})


class FetchOrUpdateView(ArticleView):
    def get(self, request: HttpRequest, full_name: str) -> HttpResponse:
        # find page
        article = articles.get_article(full_name)
        if article is None:
            raise APIError('Страница не найдена', 404)

        # latest source
        source = articles.get_latest_source(article)

        return self.render_json(200, {
            'pageId': full_name,
            'title': article.title,
            'source': source,
            'tags': articles.get_tags(article)
        })

    @takes_json
    def put(self, request: HttpRequest, full_name: str) -> HttpResponse:
        # find page
        article = articles.get_article(full_name)
        if article is None:
            raise APIError('Страница не найдена', 404)

        if not settings.ANONYMOUS_EDITING_ENABLED and not articles.has_perm(request.user, "web.change_article", article):
            raise APIError('Недостаточно прав', 403)

        data = self.json_input

        self._validate_article_data(data, allow_partial=True)

        # check if renaming
        if data['pageId'] != full_name:
            article2 = articles.get_article(data['pageId'])
            if article2 is not None:
                raise APIError('Страница с таким ID уже существует', 409)
            articles.update_full_name(article, data['pageId'], request.user)

        # check if changing title
        if 'title' in data and data['title'] != article.title:
            articles.update_title(article, data['title'], request.user)

        # check if changing source
        if 'source' in data and data['source'] != articles.get_latest_source(article):
            articles.create_article_version(article, data['source'], request.user)

        # check if changing tags
        if 'tags' in data:
            articles.set_tags(article, data['tags'], request.user)

        return self.render_json(200, {'status': 'ok'})


class FetchLogView(APIView):
    def get(self, request: HttpRequest, full_name: str) -> HttpResponse:
        try:
            c_from = int(request.GET.get('from', '0'))
            c_to = int(request.GET.get('to', '25'))
        except ValueError:
            raise APIError('Некорректное указание ограничений списка', 400)

        log_entries, total_count = articles.get_log_entries_paged(full_name, c_from, c_to)

        output = []
        for entry in log_entries:
            output.append({
                'revNumber': entry.rev_number,
                'user': render_user_to_json(entry.user),
                'comment': entry.comment,
                'createdAt': entry.created_at.isoformat(),
                'type': entry.type,
                'meta': entry.meta
            })

        return self.render_json(200, {'count': total_count, 'entries': output})
