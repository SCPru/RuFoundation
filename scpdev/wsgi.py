"""
WSGI config for scpdev project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'scpdev.settings'


import django
django.setup()


import logging
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
from web import events

shared_articles.init()
shared_users.init()
interwiki_batcher.init()
events.preload_events()
media.symlinks_full_update()

application = get_wsgi_application()
