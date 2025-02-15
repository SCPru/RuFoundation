import os

from django.template.utils import get_app_template_dirs
from web.controllers import articles
from django.db import transaction
from pathlib import Path
from uuid import uuid4

from web.models.files import File


def _create_article(full_name, content):
    article = articles.get_article(full_name)
    if article is None:
        article = articles.create_article(full_name)
    ver = articles.create_article_version(article, content, comment='Seeding')
    return ver

def _upload_article_files(full_name, paths_list: list[Path]):
    article = articles.get_article(full_name)
    if article is None:
        article = articles.create_article(full_name)

    files = articles.get_files_in_article(article)
    new_file_names = [file.name for file in paths_list]

    for file in files:
        if file.name in new_file_names:
            articles.delete_file_from_article(article, file)

    for path in paths_list:
        _, ext = os.path.splitext(path.name)
        media_name = str(uuid4()) + ext
        new_file = File(name=path.name, media_name=media_name, article=article)
        local_media_dir = os.path.dirname(new_file.local_media_path)
        
        if not os.path.exists(local_media_dir):
            os.makedirs(local_media_dir, exist_ok=True)

        size = 0
        with open(path, 'rb') as f1:
            with open(new_file.local_media_path, 'xb') as f2:
                while chunk := f1.read(1024):
                    f2.write(chunk)
                    size += len(chunk)
        
        new_file.size = size
        articles.add_file_to_article(article, new_file)


@transaction.atomic
def run():
    seeds_dir_name = 'templates/seeds'
    source_files_suffix = '.ftml'
    for seeds_dir in get_app_template_dirs(seeds_dir_name):
        for parent, _, files in Path(seeds_dir).walk():
            for file in files:
                if file.endswith(source_files_suffix):
                    with open(Path(parent) / file, 'r', encoding='utf-8') as f:
                        source = f.read()
                        if source:
                            parent_path = Path(parent)
                            source_path = parent_path / file
                            article_name = Path(os.path.relpath(source_path, seeds_dir)).as_posix().replace('/', ':').removesuffix(source_files_suffix)
                            files_path = parent_path / ('%s.files' % file.removesuffix(source_files_suffix))
                            print('Seeding %s...' % article_name, end='')
                            _create_article(article_name, source)
                            print(' \033[92mOK\033[0m')
                            if files_path.is_dir():
                                _, _, related_files = next(files_path.walk())
                                content_for_upload = [files_path / file for file in related_files]
                                print('╚Seeding files...', end='')
                                _upload_article_files(article_name, content_for_upload)
                                print(' \033[92mOK\033[0m')
