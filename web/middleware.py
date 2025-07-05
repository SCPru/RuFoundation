from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.utils.functional import cached_property

from web.models.site import Site
from web import threadvars

import logging
import django.middleware.csrf
import urllib.parse


User = get_user_model()

class BotAuthTokenMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "Authorization" in request.headers and request.headers["Authorization"].startswith("Bearer "):
            try:
                request.user = User.objects.get(type="bot", api_key=request.headers["Authorization"][7:])
                setattr(request, 'csrf_processing_done', True)
            except User.DoesNotExist:
                pass
        return self.get_response(request)


class FixRawPathMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # normalize meta.
        # if we do not have RAW_PATH, but have RAW_URI, get path from RAW_URI.
        # if we do not have both, put at least regular path there (wrong, but won't crash)

        if 'RAW_PATH' not in request.META:
            if 'RAW_URI' in request.META:
                parsed = urllib.parse.urlparse(request.META['RAW_URI'])
                request.META['RAW_PATH'] = parsed.path
            else:
                request.META['RAW_PATH'] = request.path

        return self.get_response(request)


# This class redirects the user if they are trying to access media file using non-media host and the other way around.
# This is for cookie safety
class MediaHostMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # set current site
        with threadvars.context():
            # find site by domain+port
            raw_host = request.get_host()
            if ':' not in raw_host and 'SERVER_PORT' in request.META:
                raw_host += ':' + request.META['SERVER_PORT']
                possible_sites = Site.objects.filter(Q(domain=raw_host) | Q(media_domain=raw_host))
            else:
                possible_sites = []
            if not possible_sites:
                # find site by domain
                raw_host = request.get_host().split(':')[0]
                possible_sites = Site.objects.filter(Q(domain=raw_host) | Q(media_domain=raw_host))
                if not possible_sites:
                    if Site.objects.exists():
                        logging.warning('This domain (\'%s\') is not configured' % raw_host)
                        raise PermissionDenied()
                    else:
                        return render(request, 'no_site.html')

            site = possible_sites[0]
            threadvars.put('current_site', site)

            is_media_host = request.get_host().split(':')[0] == site.media_domain
            media_prefixes = ['local--files', 'local--code', 'local--html', 'local--theme']
            is_media_url = bool([x for x in media_prefixes if request.path.startswith(f'/{x}/')])

            if site.media_domain != site.domain:
                non_media_host = site.domain

                if is_media_host and not is_media_url:
                    return HttpResponseRedirect('//%s%s' % (non_media_host, request.get_full_path()))
                elif not is_media_host and is_media_url:
                    return HttpResponseRedirect('//%s%s' % (site.media_domain, request.get_full_path()))

            response = self.get_response(request)

            if is_media_host or (site.domain == site.media_domain and is_media_url):
                response['Access-Control-Allow-Origin'] = '*'
            else:
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'

            return response


class UserContextMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        threadvars.put('current_user', request.user)
        return self.get_response(request)


class CsrfViewMiddleware(django.middleware.csrf.CsrfViewMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = None

    @cached_property
    def csrf_trusted_origins_hosts(self):
        return [site.domain for site in Site.objects.all()]

    @cached_property
    def allowed_origins_exact(self):
        port = ':'+str(self.request.META['SERVER_PORT'])
        hosts = self.csrf_trusted_origins_hosts
        return \
            ['http://'+host+port for host in hosts] +\
            ['http://'+host for host in hosts] +\
            ['https://'+host for host in hosts]

    @cached_property
    def allowed_origin_subdomains(self):
        return dict()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        self.request = request
        return super().process_view(request, callback, callback_args, callback_kwargs)


class ForwardedPortMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['HTTP_HOST'] = request.META['HTTP_HOST'].split(':')[0]
        return self.get_response(request)


class DropWikidotAuthMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for cookie in request.COOKIES:
            if cookie in ['wikidot_token7', 'wikidot_udsession', 'WIKIDOT_SESSION_ID']:
                response.delete_cookie(cookie, path='/')
            if cookie.startswith('WIKIDOT_SESSION_ID_'):
                response.delete_cookie(cookie, path='/')
        return response


class SpyRequestMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with threadvars.context():
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            threadvars.put('current_request', request)
            threadvars.put('current_client_ip', ip)
            return self.get_response(request)