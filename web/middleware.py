from django.conf import settings
from django.http import HttpResponseRedirect


# This class redirects the user if they are trying to access media file using non-media host and the other way around.
# This is for cookie safety
class MediaHostMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.MEDIA_HOST is not None:
            is_media_host = request.get_host() == settings.MEDIA_HOST
            is_media_url = request.path.startswith(settings.MEDIA_URL)

            non_media_host = [x for x in settings.ALLOWED_HOSTS if x != settings.MEDIA_HOST][0]

            if is_media_host and not is_media_url:
                return HttpResponseRedirect('//%s%s' % (non_media_host, request.get_full_path()))
            elif not is_media_host and is_media_url:
                return HttpResponseRedirect('//%s%s' % (settings.MEDIA_HOST, request.get_full_path()))

        return self.get_response(request)