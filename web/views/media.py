import mimetypes
import os.path
from io import BufferedReader
from pathlib import Path

from django.views.static import was_modified_since
from django.http import FileResponse, Http404, HttpResponse, HttpRequest, HttpResponseNotModified
from django.conf import settings
from django.views.generic.base import View
from django.utils.http import http_date

from web.controllers import articles
from web.util.http import validate_mime

class MediaView(View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    @staticmethod
    def _partial_quote(url):
        return url.replace(':', '%3A').replace('/', '%2F').replace('?', '%3F')
    

    @staticmethod
    def _get_mime_chunk_size(mime: str):
        for accepted_mime in settings.RANGED_CONTENT_SERVING:
            if validate_mime(mime, accepted_mime):
                return settings.RANGED_CONTENT_SERVING.get(accepted_mime)
        return None
    

    @staticmethod
    def _get_file_chunk(file: BufferedReader, begin: int, end: int, max_end: int):
        begin = min(begin, max_end)
        end = min(end, max_end)

        if begin < 0 or begin >= end or end == 0:
            return None
        
        file.seek(begin)

        return file.read(end - begin)


    def get(self, request: HttpRequest, dir_path: str, *args, **kwargs):
        document_root = Path(settings.MEDIA_ROOT)
        dir_path_split = dir_path.split('/')
        content_type = None
        content_length = 0

        if not dir_path.startswith('-/'):
            # we need to check if dir path does not exist. if it doesn't, look for possible file remap (name->media_name)
            # to be changed later somehow.
            # the current setup allows serving both UUID-remapped files and avatars/etc from the same path
            document_root /= 'media'

            if len(dir_path_split) == 2:
                exists = os.path.exists(document_root / dir_path)
                if not exists:
                    article = articles.get_article(dir_path_split[0])
                    if article:
                        file = articles.get_file_in_article(article, dir_path_split[1])
                        if file:
                            dir_path_split[1] = file.media_name
                            dir_path_split[0] = article.media_name
                            content_type = file.mime_type
                            content_length = file.size

        dir_path = '/'.join([self._partial_quote(x) for x in dir_path_split])
        full_path = document_root / dir_path

        if not full_path.exists():
            raise Http404('Not found')

        stat = full_path.stat()

        if not content_type:
            content_type, encoding = mimetypes.guess_type(str(full_path))
            content_type = content_type or 'application/octet-stream'
            if encoding:
                response["Content-Encoding"] = encoding

        range = request.headers.get('Range')
        chunk_size = self._get_mime_chunk_size(content_type)

        if not chunk_size:
            return FileResponse(full_path.open('rb'), content_type=content_type)

        if not content_length:
            content_length = stat.st_size

        if not was_modified_since(
            request.META.get('HTTP_IF_MODIFIED_SINCE'),
            stat.st_mtime):
            return HttpResponseNotModified()
        
        response = HttpResponse(content_type=content_type)
        response['Last-Modified'] = http_date(stat.st_mtime)
        response['Content-Length'] = content_length
        response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range'
        response['Content-Disposition'] = 'inline'
        response['Accept-Ranges'] = 'bytes'

        begin, end = 0, min(chunk_size, content_length)
        if range:
            unit, range_str = range.split('=')

            if unit != 'bytes':
                return HttpResponse(status=416)
            
            begin, end = map(lambda a: int(a) if a else 0, range_str.split('-'))
        
            begin = min(begin, content_length)if begin else 0
            max_end = min(begin + chunk_size, content_length)
            end = min(end, max_end) if end else max_end

        content = self._get_file_chunk(full_path.open('rb'), begin, end, content_length)

        if content:
            response['Content-Range'] = f'bytes {begin}-{end-1}/{content_length}'
            response['Content-Length'] = len(content)
            response.content = content
            response.status_code = 206
        else:
            response['Content-Range'] = f'bytes */{content_length}'
            response.status_code = 416
        
        return response
