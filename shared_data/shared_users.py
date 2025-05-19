import logging
import multiprocessing
import threading
import time

from renderer.utils import render_user_to_json
from web import threadvars
from web.models.users import User


BACKGROUND_RELOAD_DELAY = 60 * 15


# These default values are used in dev server.
# When running via multiprocessing, this should be replaced with Manager by calling init() before forking.
state = None
lock = None


def background_reload():
    global state

    while True:
        try:
            with threadvars.context():
                logging.info('%s: Reloading users', threading.current_thread().ident)
                all_users = User.objects.all()
                logging.info('%s: Finished reloading users', threading.current_thread().ident)
            state['all_users'] = [render_user_to_json(user) for user in all_users]
            time.sleep(BACKGROUND_RELOAD_DELAY)
        except Exception as e:
            logging.error('Failed to background-reload users', exc_info=e)
            time.sleep(BACKGROUND_RELOAD_DELAY / 2)


def get_all_users():
    global state

    return state.get('all_users', [])


def init():
    global state, lock

    manager = multiprocessing.Manager()
    state = manager.dict()
    lock = manager.RLock()

    t = threading.Thread(target=background_reload, daemon=True)
    t.start()
