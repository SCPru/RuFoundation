from typing import Literal

from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, SearchHeadline, TrigramSimilarity
from django.core.paginator import Paginator
import shlex
from uuid import uuid4
from django.db import connection
import base64
import json

from renderer import RenderContext, single_pass_render_text
from web.controllers import articles
from web.models import ArticleSearchIndex, Article


def search_articles(text, is_source=False, cursor=None, limit=25):
    if is_source:
        cursor_parameters = decode_cursor(cursor, 'source', ['id__lt', 'id'])

        results = ArticleSearchIndex.objects
        if cursor_parameters:
            results = results.filter(cursor_parameters)
        results = results.filter(
            content_source__icontains=text,
        ).order_by('-id')[:limit]

        print(results.explain(analyze=True))

        output = []

        results = list(results)
        for article in results:
            output.append({
                'article': article,
                'words': text
            })

        if results:
            next_cursor = encode_cursor('source', [
                dict(id__lt=results[-1].id)
            ])
        else:
            next_cursor = encode_cursor('source', [
                dict(id=-1)
            ])

        return output, next_cursor
    else:
        cursor_parameters = decode_cursor(cursor, 'plain', ['rank__lt', 'rank', 'id__lt', 'id'])
        search_query_en = SearchQuery(text, config='english', search_type="websearch")
        search_query_ru = SearchQuery(text, config='russian', search_type="websearch")
        search_query = search_query_en | search_query_ru
        mark_name = str(uuid4())
        mark_open = f'<{mark_name}>'
        mark_close = f'</{mark_name}>'
        results = ArticleSearchIndex.objects
        if cursor_parameters:
            results = results.filter(cursor_parameters)
        results = results.annotate(
            rank=SearchRank(
                models.F('vector_plaintext'),
                search_query,
                cover_density=True,
                normalization=32
            ),
            headline_en=SearchHeadline(
                models.F('content_plaintext'),
                search_query,
                config='english',
                start_sel=mark_open,
                stop_sel=mark_close,
                max_words=35,
                min_words=20,
                max_fragments=3,
                fragment_delimiter=' ... '
            ),
            headline_ru=SearchHeadline(
                models.F('content_plaintext'),
                search_query,
                config='russian',
                start_sel=mark_open,
                stop_sel=mark_close,
                max_words=35,
                min_words=20,
                max_fragments=3,
                fragment_delimiter=' ... '
            )
        ).filter(
            models.Q(vector_plaintext__exact=search_query)
        ).order_by('-rank', '-id')[:limit]

        print(results.explain(analyze=True))

        output = []

        results = list(results)
        for article in results:
            highlighted_snippet = article.headline_en + article.headline_ru

            import re
            matched = re.findall(r'<%s>(.*?)</%s>' % (mark_name, mark_name), highlighted_snippet)
            article.matched_words = list(set(matched))  # Dedupe

            output.append({
                'article': article,
                'words': article.matched_words
            })

        if results:
            next_cursor = encode_cursor('plain', [
                dict(rank__lt=results[-1].rank),
                dict(rank=results[-1].rank, id__lt=results[-1].id)
            ])
        else:
            next_cursor = encode_cursor('plain', [
                dict(id=-1)
            ])

        return output, next_cursor


def decode_cursor(cursor: str | None, expected_type: Literal['source', 'plain'], whitelist=None) -> models.Q | None:
    if cursor is None:
        return None
    try:
        data = base64.b64decode(cursor).decode('utf-8')
        data = json.loads(data)
        if (expected_type == 'source' and data.get('t') == 'source') or \
                (expected_type == 'plain' and data.get('t') == 'plain'):
            options = None
            for option in data.get('o'):
                for k in option:
                    if whitelist is None or k not in whitelist:
                        del option[k]
                if options is None:
                    options = models.Q(**option)
                else:
                    options |= models.Q(**option)
            return options
        return None
    except:
        return None


def encode_cursor(cursor_type: Literal['source', 'plain'], parameters: list[dict[str, any]]) -> str:
    data = {'t': cursor_type, 'o': parameters}
    data = json.dumps(data)
    data = base64.b64encode(data.encode('utf-8')).decode('ascii')
    return data


def update_search_index(article: Article):
    version = articles.get_latest_version(article)

    if version is None:
        return

    search_obj, created = ArticleSearchIndex.objects.get_or_create(article=article)
    context = RenderContext(article=version.article, source_article=article)
    search_obj.content_source = article.title + '\n\n' + version.source
    try:
        search_obj.content_plaintext = article.title + '\n\n' + single_pass_render_text(version.source, context, 'system')
    except:
        search_obj.content_plaintext = search_obj.content_source
    search_obj.save()

    ArticleSearchIndex.objects.filter(pk=search_obj.pk).update(
        vector_plaintext=SearchVector('content_plaintext', config='english') + SearchVector('content_plaintext', config='russian')
    )
