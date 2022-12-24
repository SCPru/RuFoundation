from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseRedirect
from web.models.sites import Site
from web import threadvars
import django.middleware.csrf
import urllib.parse


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
                    raise RuntimeError('Site for this domain (\'%s\') is not configured' % raw_host)

            site = possible_sites[0]
            threadvars.put('current_site', site)

            is_media_host = request.get_host().split(':')[0] == site.media_domain
            is_media_url = request.path.startswith(settings.MEDIA_URL)

            if site.media_domain != site.domain:
                non_media_host = site.domain

                if is_media_host and not is_media_url:
                    return HttpResponseRedirect('//%s%s' % (non_media_host, request.get_full_path()))
                elif not is_media_host and is_media_url:
                    return HttpResponseRedirect('//%s%s' % (site.media_domain, request.get_full_path()))

            response = self.get_response(request)

            if not is_media_host and (site.domain != site.media_domain or not is_media_url):
                response['X-Content-Type-Options'] = 'nosniff'
            elif 'Origin' in request.headers:
                allowed_origins = ['http://%s' % site.domain, 'https://%s' % site.domain]
                origin = request.headers['Origin']
                if origin in allowed_origins:
                    response['Access-Control-Allow-Origin'] = origin

            return response


class CsrfViewMiddleware(django.middleware.csrf.CsrfViewMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = None

    @property
    def csrf_trusted_origins_hosts(self):
        return [site.domain for site in Site.objects.all()]

    @property
    def allowed_origins_exact(self):
        port = ':'+str(self.request.META['SERVER_PORT'])
        hosts = self.csrf_trusted_origins_hosts
        return \
            ['http://'+host+port for host in hosts] +\
            ['http://'+host for host in hosts] +\
            ['https://'+host for host in hosts]

    @property
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
        rsp = self.get_response(request)
        for cookie in request.COOKIES:
            if cookie in ['wikidot_token7', 'wikidot_udsession', 'WIKIDOT_SESSION_ID']:
                rsp.delete_cookie(cookie, path='/')
            if cookie.startswith('WIKIDOT_SESSION_ID_'):
                rsp.delete_cookie(cookie, path='/')
        return rsp
