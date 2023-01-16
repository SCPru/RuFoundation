"""
WSGI config for scpdev project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from shared_data import shared_articles

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scpdev.settings')

shared_articles.init()

application = get_wsgi_application()
