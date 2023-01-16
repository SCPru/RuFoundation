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

from django.core.wsgi import get_wsgi_application
from shared_data import shared_articles

shared_articles.init()

application = get_wsgi_application()
