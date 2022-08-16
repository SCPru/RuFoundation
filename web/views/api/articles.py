from django.conf import settings
from django.http import HttpRequest, HttpResponse

from renderer.nodes.link_internal import InternalLinkNode
from . import APIView, APIError, takes_json

from web.controllers import articles, permissions

from renderer.utils import render_user_to_json
from renderer import single_pass_render
from renderer.parser import RenderContext

import json

from ...models.articles import ExternalLink, Article


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
        if 'source' in data and len(data['source']) > settings.ARTICLE_SOURCE_LIMIT:
            raise APIError('Превышен лимит размера страницы')


class CreateView(ArticleView):
    @takes_json
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        data = self.json_input

        self._validate_article_data(data)

        name, category = articles.get_name(data['pageId'])
        if not permissions.check(request.user, "create", Article(category=category, name=name)):
            raise APIError('Недостаточно прав', 403)

        article = articles.get_article(data['pageId'])
        if article is not None:
            raise APIError('Страница с таким ID уже существует', 409)

        # create page
        article = articles.create_article(data['pageId'], request.user)
        article.title = data['title']
        article.save()
        version = articles.create_article_version(article, data['source'], request.user)
        articles.refresh_article_links(version)

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
            'tags': articles.get_tags(article),
            'parent': articles.get_parent(article),
            'locked': article.locked
        })

    @takes_json
    def put(self, request: HttpRequest, full_name: str) -> HttpResponse:
        # find page
        article = articles.get_article(full_name)
        if article is None:
            raise APIError('Страница не найдена', 404)

        if not permissions.check(request.user, "edit", article):
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
            version = articles.create_article_version(article, data['source'], request.user, data.get('comment', ''))
            articles.refresh_article_links(version)

        # check if changing tags
        if 'tags' in data:
            articles.set_tags(article, data['tags'], request.user)

        # check if changing parent
        if 'parent' in data:
            articles.set_parent(article, data['parent'], request.user)

        # check if lock article
        if 'locked' in data:
            if data['locked'] != article.locked:
                if permissions.check(request.user, "lock", article):
                    articles.set_lock(article, data['locked'], request.user)
                else:
                    raise APIError('Недостаточно прав', 403)

        return self.render_json(200, {'status': 'ok'})

    def delete(self, request: HttpRequest, full_name: str) -> HttpResponse:
        # find page
        article = articles.get_article(full_name)
        if article is None:
            raise APIError('Страница не найдена', 404)

        if not permissions.check(request.user, "delete", article):
            raise APIError('Недостаточно прав', 403)

        articles.delete_article(article)

        return self.render_json(200, {'status': 'ok'})


class FetchOrRevertLogView(APIView):
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

    @takes_json
    def put(self, request: HttpRequest, full_name: str) -> HttpResponse:
        article = articles.get_article(full_name)
        if article is None:
            raise APIError('Страница не найдена', 404)

        if not permissions.check(request.user, "edit", article):
            raise APIError('Недостаточно прав', 403)

        data = self.json_input

        if not ("revNumber" in data and isinstance(data["revNumber"], int)):
            raise APIError('Некорректный номер ревизии', 400)

        raise APIError('Откат правок в данный момент отключен', 409)

        # articles.revert_article_version(article, data["revNumber"], request.user)
        # version = articles.get_latest_version(article)
        # articles.refresh_article_links(version)

        # return self.render_json(200, {"pageId": article.full_name})


class FetchVersionView(APIView):
    def get(self, request: HttpRequest, full_name: str) -> HttpResponse:
        entry = articles.get_log_entry(full_name, request.GET.get('revNum'))
        if not entry:
            raise APIError('Версии с данным идентификатором не существует', 404)

        version = None
        if "version_id" in entry.meta:
            version = articles.get_version(entry.meta["version_id"])
        else:
            log_entries = list(articles.get_log_entries(full_name))
            for old_entry in log_entries[log_entries.index(entry):]:
                if "version_id" in old_entry.meta:
                    version = articles.get_version(old_entry.meta["version_id"])

        if version:
            if version.rendered:
                rendered = version.rendered
            else:
                context = RenderContext(version.article, version.article, json.loads(request.GET.get('pathParams', "{}")), self.request.user)
                rendered = single_pass_render(version.source, context)

            return self.render_json(200, {'source': version.source, "rendered":  rendered})
        raise APIError('Версии с данным идентификатором не существует', 404)


class FetchExternalLinks(APIView):
    def get(self, request: HttpRequest, full_name: str) -> HttpResponse:
        article = articles.get_article(full_name)
        if not article:
            raise APIError('Страница не найдена', 404)

        links_children = [{'id': x.full_name, 'title': x.title, 'exists': True} for x in Article.objects.filter(parent=article)]

        links_all = ExternalLink.objects.filter(link_to=full_name)

        links_include = []
        links_links = []

        articles_dict = InternalLinkNode.fetch_articles_by_names([link.link_from.lower() for link in links_all])

        for link in links_all:
            article = articles_dict.get(link.link_from.lower())
            article_record = {'id': article.full_name, 'title': article.title, 'exists': True} if article else {'id': link.link_from.lower(), 'title': link.link_from.lower(), 'exists': False}
            if link.link_type == ExternalLink.Type.Include:
                links_include.append(article_record)
            elif link.link_type == ExternalLink.Type.Link:
                links_links.append(article_record)

        return self.render_json(200, {'children': links_children, 'includes': links_include, 'links': links_links})
