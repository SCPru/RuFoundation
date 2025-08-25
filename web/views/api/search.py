from django.http import HttpRequest

from renderer.utils import render_user_to_json
from . import APIView

from web.controllers import search, articles


class SearchView(APIView):
    def get(self, request: HttpRequest):
        search_query = request.GET.get('text', '')
        cursor = request.GET.get('cursor')
        search_mode = request.GET.get('mode', 'plain')
        try:
            limit = int(request.GET.get('limit', '25'))
            if limit < 1:
                limit = 1
            if limit > 25:
                limit = 25
        except ValueError:
            limit = 25
        results, next_cursor = search.search_articles(search_query, is_source=(search_mode == 'source'), cursor=cursor, limit=limit)
        output_results = []
        for result in results:
            article = result['article'].article
            rating, votes, popularity, mode = articles.get_rating(article)
            output_results.append({
                'uid': article.id,
                'pageId': article.full_name,
                'title': article.title,
                'createdAt': article.created_at.isoformat(),
                'updatedAt': article.updated_at.isoformat(),
                'createdBy': render_user_to_json(article.author),
                'rating': {
                    'value': rating,
                    'votes': votes,
                    'popularity': popularity,
                    'mode': str(mode)
                },
                'tags': articles.get_tags(article),
                'words': result['words'],
                'excerpts': self.get_excerpts(result, search_mode == 'source')
            })
        return self.render_json(200, {
            'results': output_results,
            'cursor': next_cursor
        })

    @classmethod
    def get_excerpts(cls, result, is_source):
        original = result['article'].content_source if is_source else result['article'].content_plaintext
        original = original.split('\n\n', 1)
        if len(original) < 2:
            return []
        original = original[1]
        original_to_search = original.lower()
        words_to_search = list(sorted({x.lower() for x in result['words']}, key=lambda x: len(x), reverse=True))
        ranges = []
        offset = 30
        word_length_cutoff = 2
        has_long_words = bool([x for x in words_to_search if len(x) > word_length_cutoff])
        for word in words_to_search:
            # at least for now.
            if has_long_words and len(word) <= word_length_cutoff:
                continue
            word_positions = cls.findall(word, original_to_search)
            for position in word_positions:
                word_start = position
                word_end = len(word) + word_start
                word_start = max(0, word_start - offset)
                word_end = min(len(original_to_search), word_end + offset)
                ranges.append((len(word), word_start, word_end))
        ranges.sort(key=lambda x: x[1])
        i = 0
        while i < len(ranges) - 1:
            if ranges[i+1][1] < ranges[i][2]:
                # overlap:
                # expand this one
                # delete next one
                ranges[i] = (max(ranges[i][0], ranges[i+1][0]), ranges[i][1], ranges[i+1][2])
                del ranges[i+1]
                continue
            i += 1
        # sort by max word length in a snippet (including combined snippets). longer words = first.
        # this is so that words like 'in', 'with', etc don't fill up the entire available space, if there are OTHER words.
        ranges.sort(key=lambda x: (-x[0], x[1]), reverse=False)
        ranges = ranges[:25]
        excerpts = []
        for _, excerpt_start, excerpt_end in ranges:
            excerpts.append(original[excerpt_start:excerpt_end])
        # limit also total excerpt size returned to client
        max_excerpt_len = 1024
        combined_len = 0
        for i in range(len(excerpts)):
            combined_len += len(excerpts[i])
            if combined_len > max_excerpt_len:
                return excerpts[:i]
        return excerpts

    @classmethod
    def findall(cls, p, s):
        # returns all positions of the specified word "p" in the string "s".
        # to-do: detect if words are part of other words, and don't treat them as separate.
        i = s.find(p)
        positions = []
        while i != -1:
            positions.append(i)
            i = s.find(p, i + 1)
        return positions