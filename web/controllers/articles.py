from web.models.articles import *
import datetime
import re


# Returns (category, name) from a full name
def get_name(full_name):
    split = full_name.split(':', 1)
    if len(split) == 2:
        return split[0], split[1]
    else:
        return '_default', split[0]


def normalize_article_name(name):
    return re.sub(r'[^A-Za-z0-9\-_:]+', '-', name).lower().strip('-')


def get_article(full_name_or_article):
    if type(full_name_or_article) == str:
        full_name_or_article = full_name_or_article.lower()
        category, name = get_name(full_name_or_article)
        objects = Article.objects.filter(category=category, name=name)
        if objects:
            return objects[0]
        else:
            return None
    else:
        return full_name_or_article


def get_full_name(full_name_or_article):
    if type(full_name_or_article) == str:
        return full_name_or_article
    else:
        if full_name_or_article.category == '_default':
            return full_name_or_article.name
        else:
            return '%s:%s' % (full_name_or_article.category, full_name_or_article.name)


# Creates article with specified id. Does not add versions
def create_article(full_name):
    category, name = get_name(full_name)
    article = Article(
        category=category,
        name=name,
        created_at=datetime.datetime.now(),
        title=name
    )
    article.save()
    return article


# Adds log entry to article
def add_log_entry(full_name_or_article, log_entry):
    article = get_article(full_name_or_article)
    existing_entry = get_latest_log_entry(article)
    if existing_entry is None:
        log_entry.rev_number = 0
    else:
        log_entry.rev_number = existing_entry.rev_number + 1
    log_entry.save()


# Gets all log entries of article, sorted
def get_log_entries(full_name_or_article):
    article = get_article(full_name_or_article)
    return ArticleLogEntry.objects.filter(article=article).order_by('-rev_number')


# Gets latest log entry of article
def get_latest_log_entry(full_name_or_article):
    log_entry = get_log_entries(full_name_or_article)[:1]
    if log_entry:
        return log_entry[0]
    return None


# Gets list of log entries from article, sorted, with specified bounds
def get_log_entries_paged(full_name_or_article, c_from, c_to):
    log_entries = get_log_entries(full_name_or_article)
    total_count = len(log_entries)
    return log_entries[c_from:c_to], total_count


# Creates new article version for specified article
def create_article_version(full_name_or_article, source):
    article = get_article(full_name_or_article)
    is_new = get_latest_version(article) is None
    version = ArticleVersion(
        article=article,
        source=source,
        rendered=None
    )
    version.save()
    # either NEW or SOURCE
    if is_new:
        log = ArticleLogEntry(
            article=article,
            type=ArticleLogEntry.LogEntryType.New,
            meta={'version_id': version.id, 'title': article.title}
        )
    else:
        log = ArticleLogEntry(
            article=article,
            type=ArticleLogEntry.LogEntryType.Source,
            meta={'version_id': version.id}
        )
    add_log_entry(article, log)
    return version


# Updates name of article
def update_full_name(full_name_or_article, new_full_name):
    article = get_article(full_name_or_article)
    prev_full_name = get_full_name(full_name_or_article)
    category, name = get_name(new_full_name)
    article.category = category
    article.name = name
    article.save()
    log = ArticleLogEntry(
        article=article,
        type=ArticleLogEntry.LogEntryType.Name,
        meta={'name': new_full_name, 'prev_name': prev_full_name}
    )
    add_log_entry(article, log)


# Updates title of article
def update_title(full_name_or_article, new_title):
    article = get_article(full_name_or_article)
    prev_title = article.title
    article.title = new_title
    article.save()
    log = ArticleLogEntry(
        article=article,
        type=ArticleLogEntry.LogEntryType.Title,
        meta={'title': new_title, 'prev_title': prev_title}
    )
    add_log_entry(article, log)


# Get latest version of article
def get_latest_version(full_name_or_article):
    article = get_article(full_name_or_article)
    if article is None:
        return None
    latest_version = ArticleVersion.objects.filter(article=article).order_by('-created_at')[:1]
    if latest_version:
        return latest_version[0]
    else:
        return None


# Get latest source of article
def get_latest_source(full_name_or_article):
    ver = get_latest_version(full_name_or_article)
    if ver is not None:
        return ver.source
    else:
        return None


# Set parent of article
def set_parent(full_name_or_article, full_name_of_parent):
    article = get_article(full_name_or_article)
    parent = get_article(full_name_of_parent) if full_name_of_parent else None
    prev_parent = get_full_name(article.parent) if article.parent else None
    if article.parent == parent:
        return
    article.parent = parent
    article.save()
    log = ArticleLogEntry(
        article=article,
        type=ArticleLogEntry.LogEntryType.Parent,
        meta={'parent': full_name_of_parent, 'prev_parent': prev_parent}
    )
    add_log_entry(article, log)


# Gets all parents
def get_breadcrumbs(full_name_or_article):
    article = get_article(full_name_or_article)
    output = []
    while article:
        output.append(article)
        article = article.parent
    return list(reversed(output))


# Check if name is allowed for creation
# Pretty much this blocks two 100% special paths, everything else is OK
def is_full_name_allowed(article_name):
    if article_name == '_' or article_name == 'api':
        return False
    if len(article_name) > 128:
        return False
    if not re.match(r'^[A-Za-z0-9\-_:]+$', article_name):
        return False
    category, name = get_name(article_name)
    if not category.strip() or not name.strip():
        return False
    return True
