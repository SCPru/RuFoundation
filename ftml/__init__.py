# This module handles automatic rebuild of Rust stuff when executed from runserver --watch

import threading
import os
import platform
from pathlib import Path
import importlib
import time

_this_dir = Path(os.path.dirname(__file__))
_last_ftml_time = None
ftml = None


def reload_ftml(once=False):
    global _last_ftml_time
    global ftml
    while True:
        if platform.system() == 'Windows':
            filename = 'ftml.pyd'
        else:
            filename = 'ftml.so'
        if not os.path.exists(_this_dir / filename):
            cur_time = None
        else:
            cur_time = os.path.getmtime(_this_dir / filename)
        if cur_time is not None and cur_time != _last_ftml_time:
            if _last_ftml_time is None:
                ftml = importlib.import_module('ftml.ftml', 'ftml')
            else:
                ftml = importlib.reload(ftml)
            _last_ftml_time = cur_time
        time.sleep(1)
        if once:
            break


reload_ftml(once=True)

t = threading.Thread(target=reload_ftml)
t.daemon = True
t.start()

