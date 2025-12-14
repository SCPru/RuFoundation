import logging
import multiprocessing
import threading
import time

from django.db.models import Subquery, OuterRef

from renderer.utils import render_user_to_json

from web import threadvars
from web.controllers import articles
from web.models.articles import ArticleLogEntry, Article
from web.models.settings import Settings
from web.models.site import Site, get_current_site


BACKGROUND_RELOAD_DELAY = 60 * 15


# These default values are used in dev server.
# When running via multiprocessing, this should be replaced with Manager by calling init() before forking.
state = None
lock = None


def reload_once(site):
    latest_entries_sq = ArticleLogEntry.objects.filter(
        article_id=OuterRef('article_id')
    ).order_by('-rev_number')

    latest_events_qs = ArticleLogEntry.objects.filter(
        pk=Subquery(latest_entries_sq.values('pk')[:1])
    ).select_related(
        'user'
    ).prefetch_related(
        'user__roles',
        'user__roles__permissions',
        'user__roles__restrictions'
    )

    last_events = {e.article_id: e for e in latest_events_qs}

    db_articles_qs = (
        Article.objects
        .prefetch_related(
            'votes',
            'tags',
            'tags__category',
            'authors',
            'authors__roles',
            'authors__roles__permissions',
            'authors__roles__restrictions'
        )
        
    )

    ratings_map = articles.get_all_ratings(db_articles_qs)

    _users_cache = {}
    def _get_user_json_cached(user):
        nonlocal _users_cache
        if user in _users_cache:
            return _users_cache[user]
        _users_cache[user] = render_user_to_json(user)
        return _users_cache[user]

    stored_articles = {}
    for article in db_articles_qs:
        last_event = last_events.get(article.id)
        rating, rating_votes, popularity, rating_mode = ratings_map.get(article.id, (0, 0, 0, Settings.RatingMode.Disabled))
        
        authors = list(article.authors.all())
        authors = [_get_user_json_cached(author) for author in authors] if authors else [_get_user_json_cached(None)]
        created_by = authors[0]
        updated_by = _get_user_json_cached(last_event.user)

        article_tags = list(sorted([tag.full_name.lower() for tag in article.tags.all()]))

        if article.category not in stored_articles:
            stored_articles[article.category] = []

        stored_articles[article.category].append({
            'uid': article.id,
            'pageId': article.full_name,
            'title': article.title,
            'canonicalUrl': f"//{site.domain}/{article.full_name}",
            'createdAt': article.created_at.isoformat(),
            'updatedAt': article.updated_at.isoformat(),
            'createdBy': created_by,
            'updatedBy': updated_by,
            'authors': authors,
            'rating': {
                'value': rating,
                'votes': rating_votes,
                'popularity': popularity,
                'mode': str(rating_mode)
            },
            'tags': article_tags
        })
        
    return stored_articles

def background_reload():
    global state

    while True:
        try:
            site = Site.objects.get()
            with threadvars.context():
                threadvars.put('current_site', site)
                logging.info('Shared worker (%s): Reloading articles for %s', threading.current_thread().ident, site.slug)

                stored_articles = reload_once(site)

                logging.info('Shared worker (%s): Finished reloading articles for %s', threading.current_thread().ident, site.slug)
            state[site.slug] = stored_articles
            time.sleep(BACKGROUND_RELOAD_DELAY)
        except Exception as e:
            logging.error('Shared worker (%s): Failed to background-reload articles', threading.current_thread().ident, exc_info=e)
            time.sleep(BACKGROUND_RELOAD_DELAY / 2)


def get_all_articles() -> dict[str, list]:
    global state

    site = get_current_site()
    return state.get(site.slug, {})


def init():
    global state, lock

    manager = multiprocessing.Manager()
    state = manager.dict()
    lock = manager.RLock()

    t = threading.Thread(target=background_reload, daemon=True)
    t.start()
