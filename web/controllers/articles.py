from django.contrib.auth.models import AbstractUser as _UserType
from django.db.models import QuerySet
from django.db import transaction
from web.models.articles import *
from web.models.files import *

from typing import Optional, Union, Sequence, Tuple
import datetime
import re
import os.path


_FullNameOrArticle = Optional[Union[str, Article]]
_FullNameOrCategory = Optional[Union[str, Category]]


# Returns (category, name) from a full name
def get_name(full_name: str) -> Tuple[str, str]:
    split = full_name.split(':', 1)
    if len(split) == 2:
        return split[0], split[1]
    return '_default', split[0]


def normalize_article_name(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9\-_:]+', '-', name).lower().strip('-')


def get_article(full_name_or_article: _FullNameOrArticle) -> Optional[Article]:
    if full_name_or_article is None:
        return None
    if type(full_name_or_article) == str:
        full_name_or_article = full_name_or_article.lower()
        category, name = get_name(full_name_or_article)
        objects = Article.objects.filter(category__iexact=category, name__iexact=name)
        if objects:
            return objects[0]
        else:
            return None
    if not isinstance(full_name_or_article, Article):
        raise ValueError('Expected str or Article')
    return full_name_or_article


def get_full_name(full_name_or_article: _FullNameOrArticle) -> str:
    if full_name_or_article is None:
        return ''
    if type(full_name_or_article) == str:
        return full_name_or_article
    return full_name_or_article.full_name


# Creates article with specified id. Does not add versions
def create_article(full_name: str) -> Article:
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
def add_log_entry(full_name_or_article: _FullNameOrArticle, log_entry: ArticleLogEntry):
    article = get_article(full_name_or_article)
    existing_entry = get_latest_log_entry(article)
    if existing_entry is None:
        log_entry.rev_number = 0
    else:
        log_entry.rev_number = existing_entry.rev_number + 1
    log_entry.save()


# Gets all log entries of article, sorted
def get_log_entries(full_name_or_article: _FullNameOrArticle) -> QuerySet[ArticleLogEntry]:
    article = get_article(full_name_or_article)
    return ArticleLogEntry.objects.filter(article=article).order_by('-rev_number')


# Gets latest log entry of article
def get_latest_log_entry(full_name_or_article: _FullNameOrArticle) -> Optional[ArticleLogEntry]:
    log_entry = get_log_entries(full_name_or_article)[:1]
    if log_entry:
        return log_entry[0]
    return None


# Gets list of log entries from article, sorted, with specified bounds
def get_log_entries_paged(full_name_or_article: _FullNameOrArticle, c_from: int, c_to: int) -> Tuple[QuerySet[ArticleLogEntry], int]:
    log_entries = get_log_entries(full_name_or_article)
    total_count = len(log_entries)
    return log_entries[c_from:c_to], total_count


# Revert all revisions to specific revision
@transaction.atomic
def revert_article_version(full_name_or_article: _FullNameOrArticle, rev_number: int, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    latest = get_latest_log_entry(article)

    rev_number += 1
    if latest.rev_number > rev_number:
        for entry in get_log_entries(article):
            if entry.type == ArticleLogEntry.LogEntryType.Source:
                create_article_version(article, get_version(entry.meta['version_id']).source, user)
            elif entry.type == ArticleLogEntry.LogEntryType.Title:
                update_title(article, entry.meta["prev_title"], user)
            elif entry.type == ArticleLogEntry.LogEntryType.Name:
                if not get_article(entry.meta["prev_name"]):
                    update_full_name(article, entry.meta["prev_name"], user)
            elif entry.type == ArticleLogEntry.LogEntryType.Tags:
                tags = list(get_tags(article))
                for tag in entry.meta["added_tags"]:
                    if tag in tags:
                        tags.remove(tag)
                for tag in entry.meta["removed_tags"]:
                    tags.append(tag)
                set_tags(article, tags, user)
            elif entry.type == ArticleLogEntry.LogEntryType.New:
                update_title(article, entry.meta["title"], user)
                create_article_version(article, get_version(entry.meta['version_id']).source, user)
                break
            elif entry.type == ArticleLogEntry.LogEntryType.Parent:
                set_parent(article, entry.meta["prev_parent"], user)
            elif entry.type == ArticleLogEntry.LogEntryType.FileAdded:
                delete_file_from_article(article, get_file_in_article(article, entry.meta["name"]), user)
            elif entry.type == ArticleLogEntry.LogEntryType.FileDeleted:
                restore_file_from_article(article, get_file_in_article(article, entry.meta["name"], allow_deleted=True), user)
            elif entry.type == ArticleLogEntry.LogEntryType.FileRenamed:
                rename_file_in_article(article, get_file_in_article(article, entry.meta["name"]), entry.meta["prev_name"], user)

            if entry.rev_number == rev_number:
                break


# Creates new article version for specified article
def create_article_version(full_name_or_article: _FullNameOrArticle, source: str, user: Optional[_UserType] = None, comment: str = "") -> ArticleVersion:
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
            user=user,
            type=ArticleLogEntry.LogEntryType.New,
            meta={'version_id': version.id, 'title': article.title},
            comment=comment
        )
    else:
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.Source,
            meta={'version_id': version.id},
            comment=comment
        )
    add_log_entry(article, log)
    return version


# Updates name of article
def update_full_name(full_name_or_article: _FullNameOrArticle, new_full_name: str, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    prev_full_name = get_full_name(full_name_or_article)
    category, name = get_name(new_full_name)
    article.category = category
    article.name = name
    article.save()
    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.Name,
        meta={'name': new_full_name, 'prev_name': prev_full_name}
    )
    add_log_entry(article, log)


# Updates title of article
def update_title(full_name_or_article: _FullNameOrArticle, new_title: str, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    prev_title = article.title
    article.title = new_title
    article.save()
    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.Title,
        meta={'title': new_title, 'prev_title': prev_title}
    )
    add_log_entry(article, log)


# Get specific entry of article
def get_log_entry(full_name_or_article: _FullNameOrArticle, rev_number: int) -> Optional[ArticleLogEntry]:
    try:
        article = get_article(full_name_or_article)
        return ArticleLogEntry.objects.get(article=article, rev_number=rev_number)
    except ArticleLogEntry.DoesNotExist:
        pass


# Get specific version of article
def get_version(version_id: int) -> Optional[ArticleVersion]:
    try:
        return ArticleVersion.objects.get(id=version_id)
    except ArticleVersion.DoesNotExist:
        pass


# Get latest version of article
def get_latest_version(full_name_or_article: _FullNameOrArticle) -> Optional[ArticleVersion]:
    article = get_article(full_name_or_article)
    if article is None:
        return None
    latest_version = ArticleVersion.objects.filter(article=article).order_by('-created_at')[:1]
    if latest_version:
        return latest_version[0]


# Get latest source of article
def get_latest_source(full_name_or_article: _FullNameOrArticle) -> Optional[str]:
    ver = get_latest_version(full_name_or_article)
    if ver is not None:
        return ver.source


# Get parent of article
def get_parent(full_name_or_article: _FullNameOrArticle) -> Optional[str]:
    article = get_article(full_name_or_article)
    if article is not None and article.parent:
        return article.parent.full_name


# Set parent of article
def set_parent(full_name_or_article: _FullNameOrArticle, full_name_of_parent: _FullNameOrArticle, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    parent = get_article(full_name_of_parent) if full_name_of_parent else None
    prev_parent = get_full_name(article.parent) if article.parent else None
    if article.parent == parent:
        return
    article.parent = parent
    article.save()
    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.Parent,
        meta={'parent': full_name_of_parent, 'prev_parent': prev_parent}
    )
    add_log_entry(article, log)


# Gets all parents
def get_breadcrumbs(full_name_or_article: _FullNameOrArticle) -> Sequence[Article]:
    article = get_article(full_name_or_article)
    output = []
    while article:
        output.append(article)
        article = article.parent
    return list(reversed(output))


# Get page category
def get_category(full_name_or_category: _FullNameOrCategory) -> Optional[Category]:
    if type(full_name_or_category) == str:
        try:
            return Category.objects.get(name=full_name_or_category)
        except Category.DoesNotExist:
            return
    return full_name_or_category


def get_article_category(full_name_or_article: _FullNameOrArticle) -> Optional[Category]:
    name = get_name(full_name_or_article)[0] if type(full_name_or_article) == str else full_name_or_article.category
    return get_category(name)


# Tag name validation
def is_tag_name_allowed(name: str) -> bool:
    return ' ' not in name


# Get tags from article
def get_tags(full_name_or_article: _FullNameOrArticle) -> Sequence[str]:
    article = get_article(full_name_or_article)
    if article:
        return sorted([x.name.lower() for x in article.tags.all()])
    return []


# Set tags for article
def set_tags(full_name_or_article: _FullNameOrArticle, tags: Sequence[str], user: Optional[_UserType] = None, log: bool = True):
    article = get_article(full_name_or_article)
    article_tags = article.tags.all()
    tags = [Tag.objects.get_or_create(name=x.lower())[0] for x in tags if is_tag_name_allowed(x)]

    removed_tags = []
    added_tags = []

    for tag in article_tags:
        if tag not in tags:
            article.tags.remove(tag)
            removed_tags.append(tag.name)
            if not tag.articles:
                tag.delete()

    for tag in tags:
        if tag not in article_tags:
            # possibly create the tag here
            article.tags.add(tag)
            added_tags.append(tag.name)

    if (removed_tags or added_tags) and log:
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.Tags,
            meta={'added_tags': added_tags, 'removed_tags': removed_tags}
        )
        add_log_entry(article, log)


# Get article rating
def get_rating(full_name_or_article: _FullNameOrArticle) -> int:
    article = get_article(full_name_or_article)
    return sum([vote.rate for vote in Vote.objects.filter(article=article) if vote])


def add_vote(full_name_or_article: _FullNameOrArticle, user: settings.AUTH_USER_MODEL, rate: int):
    if rate not in [-1, 0, 1]:
        raise ValueError(f"Rate {rate} is not valid")

    article = get_article(full_name_or_article)

    try:
        user_vote = Vote.objects.get(article=article, user=user)
        if user_vote.rate == rate:
            return
        user_vote.delete()
    except Vote.DoesNotExist:
        pass
    finally:
        if rate:
            Vote(article=article, user=user, rate=rate).save()


# Set article lock status
def set_lock(full_name_or_article: _FullNameOrArticle, locked: bool, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    article.locked = locked
    article.save()


# Get file in article
def get_file_in_article(full_name_or_article: _FullNameOrArticle, file_name: str, allow_deleted: bool = False) -> Optional[File]:
    article = get_article(full_name_or_article)
    if article is None:
        return None
    files = File.objects.filter(article=article, name__iexact=file_name)
    if not allow_deleted:
        files = files.filter(deleted_at__isnull=True)
    if not files:
        return None
    return files[0]


# Get file(s) in article
def get_files_in_article(full_name_or_article: _FullNameOrArticle) -> Sequence[File]:
    article = get_article(full_name_or_article)
    if article is None:
        return []
    files = File.objects.filter(article=article, deleted_at__isnull=True)
    return files


# Add file to article
def add_file_to_article(full_name_or_article: _FullNameOrArticle, file: File, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    if file.article and file.article != article:
        raise ValueError('File already belongs to an article')
    file.article = article
    file.save()
    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.FileAdded,
        meta={'name': file.name}
    )
    add_log_entry(article, log)


# Delete file from article.
# Permanent deletion is irreversible and should not be used unless for technical cleanup purposes or from admin panel.
# We also cannot track who performed a permanent deletion.
def delete_file_from_article(full_name_or_article: _FullNameOrArticle, file: File, user: Optional[_UserType] = None, permanent = False):
    article = get_article(full_name_or_article)
    if file.article != article:
        raise ValueError(f'File article "{get_full_name(article)}" is not the same as "{article.full_name}" for deletion')
    if file.deleted_at and not permanent:
        raise ValueError('File is already deleted')
    if permanent:
        if os.path.exists(file.local_media_path):
            os.unlink(file.local_media_path)
        file.delete()
    else:
        file.deleted_at = datetime.datetime.now()
        file.deleted_by = user
        file.save()
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.FileDeleted,
            meta={'name': file.name}
        )
        add_log_entry(article, log)


# Restore deleted file to article
def restore_file_from_article(full_name_or_article: _FullNameOrArticle, file: File, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    if file.article != article:
        raise ValueError(f'File article "{get_full_name(article)}" is not the same as "{article.full_name}" for restoration')
    if not file.deleted_at:
        raise ValueError('File is not deleted')
    file.deleted_at = None
    file.deleted_by = None
    file.save()
    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.FileAdded,
        meta={'name': file.name}
    )
    add_log_entry(article, log)


# Rename file in article
def rename_file_in_article(full_name_or_article: _FullNameOrArticle, file: File, name: str, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    if file.article != article:
        raise ValueError(f'File article "{get_full_name(article)}" is not the same as "{article.full_name}" for renaming')
    old_name = file.name
    file.name = name
    file.save()
    if file.name != old_name:
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.FileRenamed,
            meta={'name': file.name, 'prev_name': old_name}
        )
        add_log_entry(article, log)


# Has user permissions for do anything with article
def has_perm(user: _UserType, perm: str, full_name_or_article: _FullNameOrArticle = None) -> bool:
    if full_name_or_article:
        article = get_article(full_name_or_article)
        category = get_article_category(article)
        if not (article.locked and perm in ("web.add_article", "web.change_article", "web.delete_article")) \
                or has_perm(user, "web.can_lock_article", article):
            return user.has_perm(f"{perm}_in_category", category) or user.has_perm(perm, article)
        return False
    return user.has_perm(perm)


def has_category_perm(user: _UserType, perm: str, full_name_or_category: _FullNameOrCategory) -> bool:
    category = get_category(full_name_or_category)
    return has_perm(user, f"{perm}_in_category") or user.has_perm(f"{perm}_in_category", category)


# Check if name is allowed for creation
# Pretty much this blocks six 100% special paths, everything else is OK
def is_full_name_allowed(article_name: str) -> bool:
    reserved = ['-', '_', 'api', 'forum', 'local--files', 'local--code']
    if article_name in reserved:
        return False
    if len(article_name) > 128:
        return False
    if not re.match(r'^[A-Za-z0-9\-_:]+$', article_name):
        return False
    category, name = get_name(article_name)
    if not category.strip() or not name.strip():
        return False
    return True
