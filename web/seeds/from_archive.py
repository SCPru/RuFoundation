import py7zr
import shutil
import os, os.path
import json
from web.controllers import articles
import time
import codecs


# NOTE: This specific seed file requires py7zr to run.
# This is not characteristic of the rest of the app, so just install it manually if needed


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
    allfiles = os.listdir('%s/meta/pages' % base_path)
    for f in allfiles:
        cnt += 1
        with codecs.open('%s/meta/pages/%s' % (base_path, f), 'r', encoding='utf-8') as fp:
            meta = json.load(fp)
            pagename = meta['name']
            title = meta['title'] if 'title' in meta else None
            top_rev = meta['last_revision']
            fn_7z = '.'.join(f.split('.')[:-1]) + '.7z'
            fn_7z = '%s/pages/%s' % (base_path, fn_7z)
            if not os.path.exists(fn_7z):
                continue
            with py7zr.SevenZipFile(fn_7z) as z:
                [(_, bio)] = z.read(['%d.txt' % top_rev]).items()
                content = bio.read().decode('utf-8')
                article = articles.create_article(pagename)
                if title is not None:
                    article.title = title
                    article.save()
                articles.create_article_version(article, content)
        if time.time() - t > 1:
            print('Added: %d/%d' % (cnt, len(allfiles)))
            t = time.time()
