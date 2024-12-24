import logging
import multiprocessing
import threading
import time

from renderer.utils import render_user_to_json
from web import threadvars
from web.controllers import articles
from web.models.articles import ArticleLogEntry, Article
from web.models.sites import Site, get_current_site


BACKGROUND_RELOAD_DELAY = 60 * 15


# These default values are used in dev server.
# When running via multiprocessing, this should be replaced with Manager by calling init() before forking.
state = None
lock = None


def background_reload():
    global state

    while True:
        try:
            sites = Site.objects.all()
            for site in sites:
                with threadvars.context():
                    threadvars.put('current_site', site)
                    logging.info('%s: Reloading articles for %s', threading.current_thread().ident, site.slug)
                    db_articles = Article.objects.prefetch_related("votes", "tags")
                    stored_articles = []
                    for article in db_articles:
                        last_event = ArticleLogEntry.objects.filter(article=article).order_by('-rev_number')[0]
                        rating, rating_votes, popularity, rating_mode = articles.get_rating(article)
                        stored_articles.append({
                            'uid': article.id,
                            'pageId': article.full_name,
                            'title': article.title,
                            'canonicalUrl': '//%s/%s' % (site.domain, article.full_name),
                            'createdAt': article.created_at.isoformat(),
                            'updatedAt': article.updated_at.isoformat(),
                            'createdBy': render_user_to_json(article.author),
                            'updatedBy': render_user_to_json(last_event.user),
                            'rating': {
                                'value': rating,
                                'votes': rating_votes,
                                'popularity': popularity,
                                'mode': str(rating_mode)
                            },
                            'tags': articles.get_tags(article)
                        })
                    logging.info('%s: Finished reloading articles for %s', threading.current_thread().ident, site.slug)
                state[site.slug] = stored_articles
            with lock:
                nonexistent_sites = [k for k in state.keys() if k not in [site.slug for site in sites]]
                for site in nonexistent_sites:
                    del state[site]
            time.sleep(BACKGROUND_RELOAD_DELAY)
        except Exception as e:
            logging.error('Failed to background-reload pages', exc_info=e)
            time.sleep(BACKGROUND_RELOAD_DELAY / 2)


def get_all_articles():
    global state

    site = get_current_site()
    return state.get(site.slug, [])


def init():
    global state, lock

    manager = multiprocessing.Manager()
    state = manager.dict()
    lock = manager.RLock()

    t = threading.Thread(target=background_reload, daemon=True)
    t.start()
