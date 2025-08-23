from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank
import shlex

from web.models import ArticleSearchIndex


def search_articles(text, is_source=False):
    # todo: use words in query
    positive_words, negative_words = split_query(text)
    field = 'content_source' if is_source else 'content_plaintext'
    search_query_en = SearchQuery(text, config='english')
    search_query_ru = SearchQuery(text, config='russian')
    results = ArticleSearchIndex.objects.annotate(
        rank_en=SearchRank('vector_plaintext_en', search_query_en),
        rank_ru=SearchRank('vector_plaintext_ru', search_query_ru),
        combined_rank=models.ExpressionWrapper(
            models.F('rank_en') + models.F('rank_ru'),
            output_field=models.FloatField()
        )
    ).filter(
        models.Q(vector_plaintext_en__exact=search_query_en) |
        models.Q(vector_plaintext_ru__exact=search_query_ru)
        #models.Q(**{field+'__icontains': text})
    ).order_by('-combined_rank')
    return results


def split_query(text):
    negative = []
    positive = []
    for word in shlex.split(text):
        if not word:
            continue
        if word[0] == '-':
            negative.append(word[1:])
        else:
            positive.append(word)
    return positive, negative
