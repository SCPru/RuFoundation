import py7zr
import shutil
import os, os.path
import json
from web.controllers import articles
import time
import codecs
import datetime


# NOTE: This specific seed file requires py7zr to run.
# This is not characteristic of the rest of the app, so just install it manually if needed


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


def run(base_path):
    # unpacks wikidot archive in DBotThePony's backup format
    # files are just copied
    base_path = base_path.rstrip('/')
    from_files = '%s/files/' % base_path
    to_files = './files/'
    print('Copying files...')
    shutil.copytree(from_files, to_files, dirs_exist_ok=True)
    print('Adding articles...')
    t = time.time()
    cnt = 0
    pages = maybe_load_pages_meta(base_path)
    for meta in pages:
        cnt += 1
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
        with py7zr.SevenZipFile(fn_7z) as z:
            [(_, bio)] = z.read(['%d.txt' % top_rev]).items()
            content = bio.read().decode('utf-8')
            article = articles.create_article(pagename)
            article.created_at = created_at
            article.updated_at = updated_at
            if title is not None:
                article.title = title
            article.save()
            articles.create_article_version(article, content)
            if tags:
                articles.set_tags(article, tags)
        if time.time() - t > 1:
            print('Added: %d/%d' % (cnt, len(pages)))
            t = time.time()
    set_parents(pages)


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
    print(repr(page_renames))

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
                        print('Parent was renamed: %s -> %s' % (rename[1], parent))
                        parent = rename[2]
                break

        article = articles.get_article(pagename)
        if article:
            if parent:
                print('Parent: %s -> %s' % (pagename, parent))
            articles.set_parent(article, parent or None)
