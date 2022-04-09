from web.models.articles import *
import datetime


# Returns (category, name) from a full name
def get_name(full_name):
    split = full_name.split(':', 1)
    if len(split) == 2:
        return split[0], split[1]
    else:
        return '_default', split[0]


def get_article(full_name_or_article):
    if type(full_name_or_article) == str:
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
    log.save()
    return version


# Updates name of article
def update_full_name(full_name_or_article, new_full_name):
    article = get_article(full_name_or_article)
    category, name = get_name(new_full_name)
    article.category = category
    article.name = name
    article.save()
    log = ArticleLogEntry(
        article=article,
        type=ArticleLogEntry.LogEntryType.Name,
        meta={'name': new_full_name}
    )
    log.save()


# Updates title of article
def update_title(full_name_or_article, new_title):
    article = get_article(full_name_or_article)
    article.title = new_title
    article.save()
    log = ArticleLogEntry(
        article=article,
        type=ArticleLogEntry.LogEntryType.Title,
        meta={'title': new_title}
    )
    log.save()


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


# Check if name is allowed for creation
# Pretty much this blocks two 100% special paths, everything else is OK
def is_full_name_allowed(article_name):
    if article_name == '_' or article_name == 'api':
        return False
    if len(article_name) > 128:
        return False
    category, name = get_name(article_name)
    if not category.strip() or not name.strip():
        return False
    return True
