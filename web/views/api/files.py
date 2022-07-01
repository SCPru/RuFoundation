from django.http import HttpRequest
import os.path
from uuid import uuid4

from . import APIView, APIError, takes_json

from web.controllers import articles

from ...models.files import File


class FileView(APIView):
    @staticmethod
    def _validate_request(request: HttpRequest, article_name):
        article = articles.get_article(article_name)
        if article is None:
            raise APIError('Страница не найдена', 404)
        if not articles.has_perm(request.user, "web.change_article", article):
            raise APIError('Недостаточно прав', 403)
        return article


class UploadView(FileView):
    def post(self, request: HttpRequest, article_name):
        article = self._validate_request(request, article_name)
        file_name = request.headers.get('x-file-name')
        if not file_name:
            raise APIError('Отсутствует название файла', 400)
        existing_file = articles.get_file_in_article(article, file_name)
        if existing_file:
            raise APIError('Файл с таким именем уже существует', 409)
        _, ext = os.path.splitext(file_name)
        media_name = str(uuid4()) + ext
        new_file = File(name=file_name, media_name=media_name, author=request.user)
        local_media_dir = os.path.basename(new_file.local_media_path)
        if not os.path.exists(local_media_dir):
            os.makedirs(local_media_dir, exist_ok=True)
        # upload file to temporary storage
        try:
            size = 0
            with open(new_file.local_media_path, 'wb') as f:
                while True:
                    chunk = request.read(102400)
                    size += len(chunk)
                    if not chunk:
                        break
                    f.write(chunk)
            new_file.size = size
            new_file.mime_type = request.headers.get('content-type', 'application/octet-stream')
            articles.add_file_to_article(article, new_file, user=request.user)
        except:
            if os.path.exists(new_file.local_media_path):
                os.unlink(new_file.local_media_path)
        return self.render_json(200, {'status': 'ok'})


class RenameOrDeleteView(FileView):
    def delete(self, request: HttpRequest, article_name, file_name):
        article = self._validate_request(request, article_name)
        file = articles.get_file_in_article(article, file_name)
        if file is None:
            raise APIError('Файл не существует', 404)
        articles.delete_file_from_article(article, file, user=request.user)
        return self.render_json(200, {'status': 'ok'})

    @takes_json
    def put(self, request: HttpRequest, article_name, file_name):
        article = self._validate_request(request, article_name)
        file = articles.get_file_in_article(article, file_name)
        if file is None:
            raise APIError('Файл не существует', 404)
        data = self.json_input
        if not isinstance(data, dict) or 'name' not in data:
            raise APIError('Некорректный запрос', 400)
        articles.rename_file_in_article(article, file, data['name'], user=request.user)
        return self.render_json(200, {'status': 'ok'})
