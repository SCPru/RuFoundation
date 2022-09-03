import io
import json
import logging
import os
import codecs
import threading
import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from django import db
from py7zr import py7zr

from .from_archive import run_in_threads, get_or_create_user, init_users
from .. import threadvars
from ..models.forum import ForumSection, ForumCategory, ForumThread, ForumPost, ForumPostVersion


def count_posts(posts):
    p = len(posts)
    for post in posts:
        if 'children' in post:
            p += count_posts(post['children'])
    return p


def post_filenames(posts):
    filenames = []
    for post in posts:
        filenames.append('%d/latest.html' % post['id'])
        if 'revisions' in post:
            for rev in post['revisions']:
                filenames.append('%d/%d.html' % (post['id'], rev['id']))
        if 'children' in post:
            filenames += post_filenames(post['children'])
    return filenames


def post_highest_timestamp(posts):
    ts = 0
    for post in posts:
        ts = max(ts, post['stamp'])
        if 'children' in post:
            ts = max(post_highest_timestamp(post['children']) or ts, ts)
    return ts


def run(base_path):
    g_users, g_users_by_username = init_users(base_path)

    logging.info('Loading categories...')
    categories = {}
    for category_file in os.listdir('%s/meta/forum/category' % base_path):
        with codecs.open('%s/meta/forum/category/%s' % (base_path, category_file), encoding='utf-8') as f:
            category = json.load(f)
            category['threads'] = []
            category['local'] = None
            categories[category['id']] = category

    t = time.time()
    t_lock = threading.RLock()

    total_threads = 0
    total_posts = 0
    done_threads = 0
    done_posts = 0
    threads = []

    for category_id, category in categories.items():
        logging.info('Loading threads for "%s"...', category['title'])
        for thread_file in os.listdir('%s/meta/forum/%d' % (base_path, category['id'])):
            with codecs.open('%s/meta/forum/%d/%s' % (base_path, category['id'], thread_file), encoding='utf-8') as f:
                thread = json.load(f)
                category['threads'].append(thread)
                thread['categoryId'] = category_id
                threads.append(thread)
                total_threads += 1
                total_posts += count_posts(thread['posts'])

    # clear the forum. this is required because we need to set IDs
    with db.connection.cursor() as cursor:
        cursor.execute('TRUNCATE TABLE web_forumsection CASCADE')

    # generate section for imported content
    section = ForumSection(name='Imported', description='Imported from archive')
    section.save()

    # generate categories
    for _, category in categories.items():
        c = ForumCategory(id=category['id'], name=category['title'], description=category['description'], section=section)
        c.save()
        category['local'] = c

    def convert_threads(work):
        nonlocal done_threads
        nonlocal done_posts
        nonlocal t

        for thread in work:
            user = get_or_create_user(thread['startedUser'], g_users, g_users_by_username)
            th = ForumThread(id=thread['id'], category=categories[thread['categoryId']]['local'], name=thread['title'], description=thread['description'], author=user, is_pinned=thread['sticky'])
            th.save()
            created_at = datetime.fromtimestamp(thread['started'], tz=timezone.utc)
            # updated_at is the highest post creation timestamp
            updated_at = datetime.fromtimestamp(post_highest_timestamp(thread['posts']) or thread['started'], tz=timezone.utc)
            ForumThread.objects.filter(id=th.id).update(created_at=created_at, updated_at=updated_at)

            post_data_7z = '%s/forum/%d/%d.7z' % (base_path, thread['categoryId'], thread['id'])

            if os.path.exists(post_data_7z):
                with py7zr.SevenZipFile(post_data_7z) as z:
                    all_file_names = post_filenames(thread['posts'])
                    post_contents = z.read(all_file_names)
            else:
                post_contents = dict()

            def add_post(post):
                nonlocal done_posts
                nonlocal t

                # create post
                user = get_or_create_user(post['poster'], g_users, g_users_by_username)
                created_at = datetime.fromtimestamp(post['stamp'], tz=timezone.utc)
                updated_at = datetime.fromtimestamp(post.get('lastEdit') or post['stamp'], tz=timezone.utc)
                p = ForumPost(id=post['id'], thread=th, name=post.get('title') or '', author=user, reply_to=post.get('replyTo', None))
                p.save()
                ForumPost.objects.filter(id=p.id).update(created_at=created_at, updated_at=updated_at)

                threadvars.put('threadid', th.id)

                if post.get('revisions', []):
                    for rev in post['revisions']:
                        rev_user = get_or_create_user(rev['author'], g_users, g_users_by_username)
                        rev_created_at = datetime.fromtimestamp(rev['stamp'], tz=timezone.utc)
                        source_in_file = '%d/%d.html' % (post['id'], rev['id'])
                        source = html_to_source(post_contents.get(source_in_file, io.BytesIO()).read().decode('utf-8'))
                        r = ForumPostVersion(post=p, author=rev_user, source=source)
                        r.save()
                        ForumPostVersion.objects.filter(id=r.id).update(created_at=rev_created_at)
                else:
                    source_in_file = '%d/latest.html' % post['id']
                    source = html_to_source(post_contents.get(source_in_file, io.BytesIO()).read().decode('utf-8'))
                    r = ForumPostVersion(post=p, author=user, source=source)
                    r.save()
                    ForumPostVersion.objects.filter(id=r.id).update(created_at=created_at)

                with t_lock:
                    done_posts += 1
                    if time.time() - t > 1:
                        logging.info(
                            'Added: %d/%d (posts: %d/%d)' % (done_threads, total_threads, done_posts, total_posts))
                        t = time.time()

                if 'children' in post:
                    for post in post['children']:
                        post['replyTo'] = p
                        add_post(post)

            for post in thread['posts']:
                add_post(post)

            with t_lock:
                done_threads += 1
                if time.time() - t > 1:
                    logging.info('Added: %d/%d (posts: %d/%d)' % (done_threads, total_threads, done_posts, total_posts))
                    t = time.time()

    run_in_threads(convert_threads, threads)
    logging.info('Done; Added: %d/%d (posts: %d/%d)' % (done_threads, total_threads, done_posts, total_posts))


####################################################################################################
# The entire following section is dedicated to conversion of HTML to Wikidot markup
####################################################################################################


def elements_to_source(iterable):
    output = ''
    for el in iterable:
        output += element_to_source(el)
    return output


def attr_value_to_source(value):
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    return value


def attrs_to_source(el, not_attrs=[]):
    output = ''
    for attr, value in el.attrs.items():
        if attr in not_attrs:
            continue
        if attr == 'class':
            value = ' '.join(value)
        value = attr_value_to_source(value)
        output += ' %s="%s"' % (attr, value)
    return output


def element_has_allowed_class(el, cls):
    if not el.attrs.get('class'):
        return True
    for c in cls:
        if c in el['class']:
            return c
    return False


def element_to_source(el):
    if isinstance(el, str):
        text = el.text
        # newlines have special meaning; newlines from here should be dropped
        text = text.replace('\n', '')
        return text
    elif el.name == 'p':
        return elements_to_source(el) + '\n\n'
    elif el.name == 'em':
        return '//' + elements_to_source(el) + '//'
    elif el.name == 'strong' or el.name == 'b':
        return '**' + elements_to_source(el) + '**'
    elif el.name == 'u':
        return '__' + elements_to_source(el) + '__'
    elif el.name == 'strike' or el.name == 's':
        return '--' + elements_to_source(el) + '--'
    elif el.name == 'sup':
        if 'footnoteref' in el.attrs.get('class', []):
            # this is not a sup, this is a footnote. find corresponding footnote in the footnote block (it must exist somewhere at root level)
            number = el.text.strip()
            root = el
            while root.parent:
                root = root.parent
            footnoteblock = root.find('div', class_='footnotes-footer')
            footnote_nodes = footnoteblock.find_all('div', class_='footnote-footer')
            footnotes = dict()
            for node in footnote_nodes:
                if '_p_text' in node.attrs and '_p_number' in node.attrs:
                    footnotes[node.attrs['_p_number']] = node.attrs['_p_text']
                else:
                    node_number = node.a.text.strip()
                    node.a.decompose()
                    children = [x for x in node]
                    children[0].replace_with(children[0][2:])
                    footnotes[node_number] = elements_to_source(node)
                    node.attrs['_p_number'] = node_number
                    node.attrs['_p_text'] = footnotes[node_number]
            gen_text = '[[footnote]]%s[[/footnote]]' % footnotes[number]
            return gen_text
        return '^^' + elements_to_source(el) + '^^'
    elif el.name == 'sub':
        return ',,' + elements_to_source(el) + ',,'
    elif el.name == 'br':
        return '\n'
    elif el.name == 'iframe':
        src = el["src"]
        return '[[iframe %s%s]]' % (src, attrs_to_source(el, ['src']))
    elif el.name == 'span':
        if 'class' in el.attrs and 'math-inline' in el['class']:
            content = el.text.strip('$').strip()
            return '[[$ %s $]]' % content
        if 'class' in el.attrs and 'equation-number' in el['class']:
            return ''
        contents = elements_to_source(el)
        attrs = attrs_to_source(el)
        return '[[span%s]]%s[[/span]]' % (attrs, contents)
    elif el.name == 'blockquote':
        contents = '> ' + '\n> '.join(elements_to_source(el).strip().split('\n')) + '\n'
        return contents
    elif el.name == 'div':
        if element_has_allowed_class(el, ['rimg', 'limg', 'cimg', 'blockquote', 'сimg', 'scpnet-progress-bar', 'scpnet-progress-bar__tick', 'block-error', 'collapsible-block-unfolded-link']):
            return '[[div%s]]\n%s[[/div]]\n' % (attrs_to_source(el), elements_to_source(el))
        elif 'collapsible-block' in el['class']:
            # detect collapsibles
            # hidelocation is not preserved
            show = el.find('div', class_='collapsible-block-folded').find('a', class_='collapsible-block-link').text.replace('\n', ' ').strip()
            hide = el.find('div', class_='collapsible-block-unfolded').find('div', class_='collapsible-block-unfolded-link').find('a', class_='collapsible-block-link').text.replace('\n', ' ').strip()
            contents = elements_to_source(el.find('div', class_='collapsible-block-content'))
            src = '[[collapsible show="%s" hide="%s"]]\n' % (attr_value_to_source(show), attr_value_to_source(hide))
            src += contents
            src += '[[/collapsible]]\n'
            return src
        elif 'yui-navset' in el['class']:
            # detect tabview
            nav = el.find('ul', class_='yui-nav').find_all('li')
            tabnames = []
            for li in nav:
                tabnames.append(li.text.replace('\n', ' ').strip())
            src = '[[tabview]]\n'
            tabs = el.find('div', class_='yui-content')
            num = 0
            for tab in tabs:
                if tab.name != 'div':
                    continue
                src += '[[tab title="%s"]]\n' % (attr_value_to_source(tabnames[num]))
                src += elements_to_source(tab)
                src += '[[/tab]]\n'
                num += 1
            src += '[[/tabview]]\n'
            return src
        elif 'code' in el['class']:
            # detect [[code]]
            if el.pre is not None:
                code = el.pre.code
                return '[[code]]\n%s\n[[code]]\n' % code
            return '[[div%s]]\n%s[[/div]]\n' % (attrs_to_source(el), elements_to_source(el))
        elif 'footnotes-footer' in el['class']:
            title = el.find('div', class_='title').text.replace('\n', ' ').strip()
            return '[[footnoteblock title="%s"]]\n' % attr_value_to_source(title)
        elif 'bibitems' in el['class']:
            title = el.find('div', class_='title').text.replace('\n', ' ').strip()
            src = '[[bibliography title="%s"]]\n' % attr_value_to_source(title)
            iv = 0
            for item in el.find_all('div', class_='bibitem'):
                iv += 1
                children = [x for x in item.children]
                children[0].replace_with(children[0][2:])
                src += ': cite%d : %s\n' % (iv, elements_to_source(item).strip())
            src += '[[/bibliography]]\n'
            return src
        elif 'image-container' in el['class']:
            # this is f>image or f<image
            prefix = ''
            if 'floatleft' in el['class']:
                prefix = 'f<'
            if 'floatright' in el['class']:
                prefix = 'f>'
            if 'alignleft' in el['class']:
                prefix = '<'
            if 'alignright' in el['class']:
                prefix = '>'
            if 'aligncenter' in el['class']:
                prefix = '='
            src = el.img["src"]
            return '[[%simage %s%s]]' % (prefix, src, attrs_to_source(el.img, ['src', 'alt']))
        elif 'content-separator' in el['class']:
            return '====\n'
        elif 'math-equation' in el['class']:
            content = el.text.strip()
            return '[[math]]\n%s\n[[/math]]\n' % content
        elif 'wiki-note' in el['class']:
            return '[[note]]\n%s[[/note]]\n' % elements_to_source(el)
        else:
            print('thread = %d' % threadvars.get('threadid'))
            raise ValueError(repr(el))
    elif el.name == 'a':
        # just generate [[a]]
        return '[[a%s]]%s[[/a]]' % (attrs_to_source(el), elements_to_source(el))
    elif el.name == 'img':
        url = el["src"]
        return '[[image %s%s]]' % (url, attrs_to_source(el, ['src', 'alt']))
    elif el.name == 'hr':
        return '----\n'
    elif el.name == 'ul' or el.name == 'li' or el.name == 'ol':
        return '[[%s]]\n%s[[/%s]]\n' % (el.name, elements_to_source(el), el.name)
    elif el.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7']:
        content = el.span.text.replace('\n', ' ').strip()
        return ('+' * int(el.name[1:])) + ' ' + content + '\n'
    elif el.name == 'tt':
        return '{{' + elements_to_source(el) + '}}'
    elif el.name == 'table':
        return '[[table%s]]\n%s[[/table]]\n' % (attrs_to_source(el), elements_to_source(el))
    elif el.name == 'tbody':
        return elements_to_source(el)
    elif el.name == 'tr':
        return '[[row%s]]\n%s[[/row]]\n' % (attrs_to_source(el), elements_to_source(el))
    elif el.name == 'td':
        return '[[cell%s]]\n%s[[/cell]]\n' % (attrs_to_source(el), elements_to_source(el))
    elif el.name == 'th':
        return '[[hcell%s]]\n%s[[/hcell]]\n' % (attrs_to_source(el), elements_to_source(el))
    elif el.name == 'script':
        return ''
    elif el.name == 'dl':
        src = ''
        for node in el:
            if node.name == 'dt':
                dd = node.find_next('dd')
                src += ': %s : %s\n' % (node.text.replace('\n', ' '), dd.text.replace('\n', ' '))
        return src
    else:
        print('thread = %d' % threadvars.get('threadid'))
        raise ValueError(repr(el))
    return ''


def html_to_source(html):
    soup = BeautifulSoup(html, features='html.parser')
    return elements_to_source(soup)
