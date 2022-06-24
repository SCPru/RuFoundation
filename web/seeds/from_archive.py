import py7zr
import shutil
import os, os.path
import sys
import json
from web.controllers import articles
import time
import codecs
import datetime
from pathlib import Path
from django.conf import settings
import math
import threading
import logging
from web import threadvars


# NOTE: This specific seed file requires py7zr to run.
# This is not characteristic of the rest of the app, so just install it manually if needed
from web.models.sites import get_current_site


def maybe_load_pages_meta(base_path_or_list):
    if type(base_path_or_list) == str:
        allfiles = os.listdir('%s/meta/pages' % base_path_or_list)
        pages = []
        for f in allfiles:
            with codecs.open('%s/meta/pages/%s' % (base_path_or_list, f), 'r', encoding='utf-8') as fp:
                meta = json.load(fp)
                meta['revisions'].sort(key=lambda x: x['revision'], reverse=True)
                meta['filename'] = f
                pages.append(meta)
        return pages
    return base_path_or_list


def run_in_threads(fn, pages):
    thread_count = 4
    per_thread_pages = []
    for i in range(thread_count):
        single_thread_cnt = int(math.ceil(len(pages) / thread_count))
        per_thread_pages.append(pages[i*single_thread_cnt:(i+1)*single_thread_cnt])
    threads = []
    site = get_current_site()
    for thread_work in per_thread_pages:
        def fn_wrapper(thread_work):
            try:
                with threadvars.context():
                    threadvars.put('current_site', site)
                    fn(thread_work)
            except:
                logging.error('Thread failed:', exc_info=True)
                sys.exit(1)
        t = threading.Thread(target=fn_wrapper, args=(thread_work,))
        t.daemon = True
        t.start()
        threads.append(t)
    while True:
        any_alive = [t for t in threads if t.is_alive()]
        if any_alive:
            time.sleep(1)
        else:
            break


def run(base_path):
    # unpacks wikidot archive in DBotThePony's backup format
    # files are just copied
    base_path = base_path.rstrip('/')
    from_files = '%s/files/' % base_path
    site = get_current_site()
    to_files = str(Path(settings.MEDIA_ROOT) / site.slug)
    if os.path.exists(to_files):
        logging.info('Removing old files...')
        shutil.rmtree(to_files, ignore_errors=False)
    logging.info('Copying files...')
    shutil.copytree(from_files, to_files, dirs_exist_ok=True)
    logging.info('Adding articles...')
    t = time.time()
    t_lock = threading.RLock()
    pages = maybe_load_pages_meta(base_path)

    total_pages = len(pages)
    total_cnt = 0

    def worker_thread(pages):
        nonlocal total_cnt
        nonlocal t
        for meta in pages:
            total_cnt += 1
            f = meta['filename']
            pagename = meta['name']
            title = meta['title'] if 'title' in meta else None
            top_rev = meta['revisions'][0]['revision']
            tags = meta['tags'] if 'tags' in meta else []
            updated_at = datetime.datetime.fromtimestamp(meta['revisions'][0]['stamp'], tz=datetime.timezone.utc)
            created_at = datetime.datetime.fromtimestamp(meta['revisions'][-1]['stamp'], tz=datetime.timezone.utc)
            fn_7z = '.'.join(f.split('.')[:-1]) + '.7z'
            fn_7z = '%s/pages/%s' % (base_path, fn_7z)
            if not os.path.exists(fn_7z):
                continue
            article = articles.get_article(pagename)
            if article:
                continue
            with py7zr.SevenZipFile(fn_7z) as z:
                [(_, bio)] = z.read(['%d.txt' % top_rev]).items()
                content = bio.read().decode('utf-8')
                article = articles.create_article(pagename)
                article.created_at = created_at
                article.updated_at = updated_at
                if title is not None:
                    article.title = title
                else:
                    article.title = ''
                article.save()
                articles.create_article_version(article, content)
                if tags:
                    articles.set_tags(article, tags)
            with t_lock:
                if time.time() - t > 1:
                    logging.info('Added: %d/%d' % (total_cnt, total_pages))
                    t = time.time()

    run_in_threads(worker_thread, pages)
    run_in_threads(set_parents, pages)


def set_parents(base_path_or_list):
    pages = maybe_load_pages_meta(base_path_or_list)
    # collect page renames
    # (max_date, name, latest)
    page_renames = []
    for meta in pages:
        for rev in meta['revisions']:
            if rev['commentary'].startswith('You successfully renamed the page: "') or\
                    rev['commentary'].startswith('Вы переименовали страницу: "'):
                renamed_from = rev['commentary'].split('"')[1]
                renamed_at = rev['stamp']
                page_renames.append((renamed_at, renamed_from, meta['name']))
    page_renames.sort(key=lambda x: x[0])

    for meta in pages:
        pagename = meta['name']
        parent = None
        for rev in meta['revisions']:
            if rev['commentary'].startswith('Parent page set to: "') or\
                    rev['commentary'].startswith('Родительской страницей установлена: "'):
                parent = rev['commentary'].split('"')[1]
                # try to find if it was renamed
                for rename in page_renames:
                    if rename[0] >= rev['stamp'] and rename[1] == parent:
                        logging.info('Parent was renamed: %s -> %s' % (rename[1], parent))
                        parent = rename[2]
                break

        article = articles.get_article(pagename)
        if article:
            if parent:
                logging.info('Parent: %s -> %s' % (pagename, parent))
            articles.set_parent(article, parent or None)
