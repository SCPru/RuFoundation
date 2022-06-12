from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseRedirect
from web.models.sites import get_current_site, Site
from web import threadvars


# This class redirects the user if they are trying to access media file using non-media host and the other way around.
# This is for cookie safety
class MediaHostMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # set current site
        with threadvars.context():
            # find site by domain
            raw_host = request.get_host().split(':')
            possible_sites = Site.objects.filter(Q(domain=raw_host) | Q(media_domain=raw_host))
            if not possible_sites:
                raise RuntimeError('Site for this domain (\'%s\') is not configured' % raw_host)

            site = possible_sites[0]
            threadvars.put('current_site', site)

            if site.media_domain != site.domain:
                is_media_host = request.get_host().split(':')[0] == site.media_domain
                is_media_url = request.path.startswith(settings.MEDIA_URL)

                non_media_host = site.domain

                if is_media_host and not is_media_url:
                    return HttpResponseRedirect('//%s%s' % (non_media_host, request.get_full_path()))
                elif not is_media_host and is_media_url:
                    return HttpResponseRedirect('//%s%s' % (site.media_domain, request.get_full_path()))

            return self.get_response(request)
