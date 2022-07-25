# NOTE: This specific seed file requires py7zr to run.
# This is not characteristic of the rest of the app, so just install it manually if needed

import py7zr
import shutil
import os, os.path
import sys
import json

from django.db import transaction

from web.controllers import articles
import time
import codecs
import datetime
from pathlib import Path
from django.conf import settings
import math
import threading
import logging
from scpdev import urls
from web import threadvars
from web.models.articles import ArticleVersion, ArticleLogEntry, Article
from web.models.files import File
from web.models.sites import get_current_site
from system.models import User
from uuid import uuid4


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


get_or_create_user_lock = threading.Lock()


@transaction.atomic
def get_or_create_user(user_name_or_id):
    with get_or_create_user_lock:
        if type(user_name_or_id) == str:
            user_name = user_name_or_id
        elif type(user_name_or_id) == int:
            user_name = 'deleted-%d' % user_name_or_id
        else:
            raise TypeError('Invalid parameter for Wikidot user: %s' % repr(user_name_or_id))
        existing = list(User.objects.filter(type=User.UserType.Wikidot, wikidot_username__iexact=user_name))
        if not existing:
            new_user = User(type=User.UserType.Wikidot, username=uuid4(), wikidot_username=user_name, is_active=False)
            new_user.save()
            return new_user
        return existing[0]


def run(base_path):
    # unpacks wikidot archive in DBotThePony's backup format
    # files are just copied
    base_path = base_path.rstrip('/')

    site = get_current_site()

    t = time.time()
    t_lock = threading.RLock()
    pages = maybe_load_pages_meta(base_path)

    total_pages = len(pages)
    total_revisions = 0
    total_files = 0
    for meta in pages:
        total_files += len(meta.get('files', []))
        total_revisions += len(meta.get('revisions', []))

    from_files = '%s/files' % base_path
    to_files = str(Path(settings.MEDIA_ROOT) / site.slug)

    if os.path.exists(to_files):
        logging.info('Removing old files...')
        shutil.rmtree(to_files, ignore_errors=False)

    def file_worker_thread(pages):
        nonlocal total_cnt
        nonlocal t

        users = {}
        for meta in pages:
            article = articles.get_article(meta['name'])
            if article is None:
                logging.warning('Missing article \'%s\' for file import', meta['name'])
                continue
            files = meta.get('files', [])
            for file in files:
                total_cnt += 1
                if file['author'] in users:
                    file_user = users[file['author']]
                else:
                    file_user = users[file['author']] = get_or_create_user(file['author'])
                from_path = '%s/%s/%d' % (from_files, urls.partial_quote(meta['name']), file['file_id'])
                _, ext = os.path.splitext(file['name'])
                media_name = str(uuid4()) + ext
                if File.objects.filter(name=file['name'], article=article):
                    logging.warning('Warn: file exists: %s/%s', meta['name'], file['name'])
                    continue
                new_file = File(
                    name=file['name'],
                    media_name=media_name,
                    author=file_user,
                    article=article,
                    mime_type=file['mime'],
                    size=file['size_bytes']
                )
                local_media_dir = os.path.dirname(new_file.local_media_path)
                if not os.path.exists(local_media_dir):
                    os.makedirs(local_media_dir, exist_ok=True)
                to_path = new_file.local_media_path
                if not os.path.exists(from_path):
                    logging.warning('Warn: file not found: %s/%s', meta['name'], file['name'])
                    continue
                shutil.copyfile(from_path, to_path)
                new_file.save()
                new_file.created_at = datetime.datetime.fromtimestamp(file['stamp'], tz=datetime.timezone.utc)
                new_file.save()
                with t_lock:
                    if time.time() - t > 1:
                        logging.info('Added: %d/%d' % (total_cnt, total_files))
                        t = time.time()

    def page_worker_thread(pages):
        nonlocal total_cnt
        nonlocal total_cnt_rev
        nonlocal t

        users = {}
        for meta in pages:
            total_cnt += 1
            f = meta['filename']
            pagename = meta['name']
            title = meta['title'] if 'title' in meta else None
            tags = meta['tags'] if 'tags' in meta else []
            updated_at = datetime.datetime.fromtimestamp(meta['revisions'][0]['stamp'], tz=datetime.timezone.utc)
            created_at = datetime.datetime.fromtimestamp(meta['revisions'][-1]['stamp'], tz=datetime.timezone.utc)
            fn_7z = '.'.join(f.split('.')[:-1]) + '.7z'
            fn_7z = '%s/pages/%s' % (base_path, fn_7z)
            if not os.path.exists(fn_7z):
                continue

            # get user for created by, updated by
            article_author = meta['revisions'][-1]['author']
            if article_author in users:
                user = users[article_author]
            else:
                user = users[article_author] = get_or_create_user(article_author)

            # create article and set tags
            article = articles.get_article(pagename)
            if article:
                logging.warning('Warn: article exists: %s', pagename)
                total_cnt_rev += len(meta.get('revisions', []))
                continue
            article = articles.create_article(pagename)
            article.author = user
            article.created_at = created_at
            if title is not None:
                article.title = title
            else:
                article.title = ''
            article.save()
            # hack to force-set updated_at field to an old value
            Article.objects.filter(pk=article.pk).update(updated_at=updated_at)
            if tags:
                articles.set_tags(article, tags, log=False)

            # add all revisions
            revisions = list(reversed(meta['revisions']))

            last_source_version = None

            with py7zr.SevenZipFile(fn_7z) as z:
                all_file_names = ['%d.txt' % x['revision'] for x in revisions if 'S' in x['flags'] or 'N' in x['flags']]
                text_revisions = z.read(all_file_names)
                for revision in revisions:
                    total_cnt_rev += 1
                    # add revision content if it's source revision
                    if revision['author'] in users:
                        user = users[revision['author']]
                    else:
                        user = users[revision['author']] = get_or_create_user(revision['author'])
                    log = ArticleLogEntry(
                        rev_number=revision['revision'],
                        article=article,
                        user=user,
                        type=ArticleLogEntry.LogEntryType.Wikidot,
                        comment=revision['commentary']
                    )
                    if 'S' in revision['flags'] or 'N' in revision['flags']:
                        content = text_revisions['%d.txt' % revision['revision']].read().decode('utf-8')
                        version = ArticleVersion(
                            article=article,
                            source=content,
                            rendered=None,
                        )
                        version.save()
                        last_source_version = version
                        log.meta = {'version_id': version.id}
                        if 'N' in revision['flags']:
                            log.type = ArticleLogEntry.LogEntryType.New
                            log.meta['title'] = article.title
                        else:
                            log.type = ArticleLogEntry.LogEntryType.Source
                    log.save()
                    log.created_at = datetime.datetime.fromtimestamp(revision['stamp'], tz=datetime.timezone.utc)
                    log.save()
                    with t_lock:
                        if time.time() - t > 1:
                            logging.info('Added: %d/%d (revisions: %d/%d)' % (total_cnt, total_pages, total_cnt_rev, total_revisions))
                            t = time.time()

            if last_source_version:
                articles.refresh_article_links(last_source_version)

            with t_lock:
                if time.time() - t > 1:
                    logging.info('Added: %d/%d (revisions: %d/%d)' % (total_cnt, total_pages, total_cnt_rev, total_revisions))
                    t = time.time()

    total_cnt = 0
    total_cnt_rev = 0
    logging.info('Adding articles...')
    run_in_threads(page_worker_thread, pages)
    total_cnt = 0
    logging.info('Adding files...')
    run_in_threads(file_worker_thread, pages)
    logging.info('Setting parents...')
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
            parent_article = articles.get_article(parent)
            if parent_article:
                article.parent = parent_article
                article.save()
