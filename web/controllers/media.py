import logging
import shutil
import threading
from pathlib import Path

from django.conf import settings

from web.models.articles import Article
from web.models.files import File


def symlinks_full_update():
    logging.info('%s: Reloading symlinks in background', threading.current_thread().ident)

    files = File.objects.filter(deleted_at__isnull=True)

    symlinks_dir = Path(settings.MEDIA_ROOT) / 'symlinks'
    rel_media_path = Path('../../media')
    rel_system_static_path = Path('../-')

    shutil.rmtree(symlinks_dir, ignore_errors=True)
    symlinks_dir.mkdir(exist_ok=True)

    try:
        system_symlinks_dir = symlinks_dir / '-'
        if not system_symlinks_dir.exists():
            system_symlinks_dir.symlink_to(rel_system_static_path, True)
        for file in files:
            try:
                link_dir: Path = symlinks_dir / file.article.full_name
                link_name = link_dir / file.name

                link_dir.mkdir(exist_ok=True)
                link_name.symlink_to(rel_media_path / file.local_media_destination)
            except FileNotFoundError:
                logging.exception(f'Failed to update symlincs for article: {file.article}')
    except:
        logging.exception('Failed to update symlinks for static')
    logging.info('%s: Finished reloading symlinks', threading.current_thread().ident)


def symlinks_article_update(article: Article, old_name: str=None):
    files = File.objects.filter(article=article, deleted_at__isnull=True)

    symlinks_dir = Path(settings.MEDIA_ROOT) / 'symlinks'
    article_dir = symlinks_dir / article.full_name
    del_name = old_name or article.full_name
    rel_media_path = Path('../../media')

    shutil.rmtree(symlinks_dir / del_name, ignore_errors=True)
    article_dir.mkdir(exist_ok=True)

    try:
        for file in files:
            try:
                link_name = article_dir / file.name
                link_name.symlink_to(rel_media_path / file.local_media_destination)
            except FileNotFoundError:
                logging.exception(f'Failed to update symlincs for article: {file.article}')
    except:
        logging.exception(f'Failed to update symlincs for article: {article}')


def symlinks_article_delete(article: Article):
    article_dir = Path(settings.MEDIA_ROOT) / 'symlinks' / article.full_name
    shutil.rmtree(article_dir, ignore_errors=True)


def update_all_symlinks_in_background():
    t = threading.Thread(target=symlinks_full_update, daemon=True)
    t.start()
