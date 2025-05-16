import logging
import os
import shutil
from pathlib import Path
from django.conf import settings

from web.models.articles import Article
from web.models.files import File


def symlinks_full_update():
    files = File.objects.filter(deleted_at__isnull=True)

    symlinks_dir = Path(settings.MEDIA_ROOT) / 'symlinks'
    shutil.rmtree(symlinks_dir, ignore_errors=True)
    symlinks_dir.mkdir(exist_ok=True)

    try:
        for file in files:
            link_dir: Path = symlinks_dir / file.article.full_name
            link_name = link_dir / file.name

            link_dir.mkdir(exist_ok=True)
            os.symlink(file.local_media_path, link_name)
    except:
        logging.error('Failed to update symlincs for articles static')


def symlinks_article_update(article: Article, old_name: str=None):
    files = File.objects.filter(article=article, deleted_at__isnull=True)

    symlinks_dir = Path(settings.MEDIA_ROOT) / 'symlinks'
    article_dir = symlinks_dir / article.full_name
    del_name = old_name or article.full_name

    shutil.rmtree(symlinks_dir / del_name, ignore_errors=True)
    article_dir.mkdir(exist_ok=True)

    try:
        for file in files:
            link_name = article_dir / file.name
            os.symlink(file.local_media_path, link_name)
    except:
        logging.error(f'Failed to update symlincs for article: {article}')


def symlinks_article_delete(article: Article):
    article_dir = Path(settings.MEDIA_ROOT) / 'symlinks' / article.full_name
    shutil.rmtree(article_dir, ignore_errors=True)
