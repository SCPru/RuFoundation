"""
WSGI config for scpdev project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'scpdev.settings'


from web.util import json
json.replace_json_dumps_default()


import django
django.setup()


import logging
logging.addLevelName(20, '==')
logging.addLevelName(30, '!!')
logging.addLevelName(40, '!!')
logging.addLevelName(50, '!!')


from web.models import Site
from django.db.utils import ProgrammingError


try:
    if not Site.objects.exists():
        logging.error('Please create site before running the server.')
except ProgrammingError:
    logging.error('Seems like you haven\'t completed migration yet. Make it and try again.')
    exit()


from django.core.wsgi import get_wsgi_application
from shared_data import shared_articles, interwiki_batcher, shared_users
from web.controllers import media
from web import permissions
from web import events


shared_articles.init()
shared_users.init()
interwiki_batcher.init()
events.preload_events()
media.update_all_symlinks_in_background()
permissions.register_role_permissions()


application = get_wsgi_application()
