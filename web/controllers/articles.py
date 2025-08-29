import shutil

from django.contrib.auth.models import AbstractUser as _UserType
from django.db import transaction
from django.db.models import QuerySet, Sum, Avg, Count, Max, TextField, Value, IntegerField, Q, F
from django.db.models.functions import Coalesce, Concat, Lower

import renderer
from web.events import EventBase
from web.models.users import User
from web.models.articles import *
from web.models.files import *

from typing import Optional, Union, Sequence, Tuple, Dict
import datetime
import re
import os.path

import unicodedata

from web.models.forum import ForumThread, ForumPost
from web.util import lock_table

from web.controllers import notifications, media


_FullNameOrArticle = Optional[Union[str, Article]]
_FullNameOrCategory = Optional[Union[str, Category]]
_FullNameOrTag = Optional[Union[str, Tag]]


class AbstractArticleEvent(EventBase, is_abstract=True):
    user: _UserType | None
    full_name_or_article: _FullNameOrArticle

    @property
    def fullname(self):
        if isinstance(self.full_name_or_article, Article):
            return self.full_name_or_article.full_name
        return self.full_name_or_article
    
    @property
    def article(self):
        if isinstance(self.full_name_or_article, str):
            self.full_name_or_article = get_article(self.full_name_or_article)
        return self.full_name_or_article


class OnVote(AbstractArticleEvent):
    old_vote: Vote | None
    new_vote: Vote | None

    @property
    def is_new(self):
        return self.new_vote != None and self.old_vote == None
    
    @property
    def is_change(self):
        return self.new_vote != None and self.old_vote != None
    
    @property
    def is_remove(self):
        return self.new_vote == None and self.old_vote != None
    

class OnCreateArticle(AbstractArticleEvent):
    pass


class OnDeleteArticle(AbstractArticleEvent):
    pass


class OnEditArticle(AbstractArticleEvent):
    log_entry: ArticleLogEntry

    @property
    def is_new(self):
        return self.log_entry.type == ArticleLogEntry.LogEntryType.New


# Returns (category, name) from a full name
def get_name(full_name: str) -> Tuple[str, str]:
    split = full_name.split(':', 1)
    if len(split) == 2:
        return split[0], split[1]
    return '_default', split[0]


def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def normalize_article_name(full_name: str) -> str:
    full_name = strip_accents(full_name.lower())
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'z',
        'з': 'z', 'и': 'i', 'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c',
        'ч': 'c', 'ы': 'i', 'э': 'e', 'ю': 'u', 'я': 'a', 'і': 'i', 'ї': 'i', 'є': 'e',
        'ь': '', 'ъ': ''
    }
    full_name = ''.join(translit_map.get(c, c) for c in full_name)
    n = re.sub(r'[^A-Za-z0-9\-_:]+', '-', full_name).strip('-')
    n = re.sub(r':+', ':', n).lower().strip(':')
    category, name = get_name(n)
    if category == '_default':
        return name
    return '%s:%s' % (category, name)


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


def deduplicate_name(full_name: str, allowed_article: Optional[Article] = None) -> str:
    i = 0
    while True:
        i += 1
        name_to_try = '%s-%d' % (full_name, i) if i > 1 else full_name
        article2 = get_article(name_to_try)
        if not article2 or (allowed_article and article2.id == allowed_article.id):
            return name_to_try


# Creates article with specified id. Does not add versions
def create_article(full_name: str, user: Optional[_UserType] = None) -> Article:
    category, name = get_name(full_name)
    article = Article(
        category=category,
        name=name,
        created_at=datetime.datetime.now(),
        title=name,
        author=user
    )
    article.save()
    OnCreateArticle(user, article).emit()
    return article


# Adds log entry to article
def add_log_entry(full_name_or_article: _FullNameOrArticle, log_entry: ArticleLogEntry):
    article = get_article(full_name_or_article)
    with transaction.atomic():
        with lock_table(ArticleLogEntry):
            # this black magic forces lock of ArticleLogEntry table on this article id,
            # so that two concurrent log entries wait for each other and are not violating unique constraint on rev_number.
            current_log = ArticleLogEntry.objects.select_related('article')\
                                                 .select_for_update()\
                                                 .filter(article=article)
            max_rev_number = current_log.aggregate(max=Max('rev_number')).get('max')
            if max_rev_number is None:
                max_rev_number = -1
            log_entry.rev_number = max_rev_number + 1
            log_entry.save()

            OnEditArticle(log_entry.user, article, log_entry).emit()

            article.updated_at = log_entry.created_at
            article.save()


# Gets all log entries of article, sorted
def get_log_entries(full_name_or_article: _FullNameOrArticle) -> QuerySet[ArticleLogEntry]:
    article = get_article(full_name_or_article)
    return ArticleLogEntry.objects.filter(article=article).order_by('-rev_number')


# Gets latest log entry of article
def get_latest_log_entry(full_name_or_article: _FullNameOrArticle) -> Optional[ArticleLogEntry]:
    return get_log_entries(full_name_or_article).first()


# Gets list of log entries from article, sorted, with specified bounds
def get_log_entries_paged(full_name_or_article: _FullNameOrArticle, c_from: int, c_to: int, get_all: bool = False) -> Tuple[QuerySet[ArticleLogEntry], int]:
    log_entries = get_log_entries(full_name_or_article)
    total_count = len(log_entries)
    if not get_all:
        log_entries = log_entries[c_from:c_to]
    return log_entries, total_count


# Revert all revisions to specific revision
def revert_article_version(full_name_or_article: _FullNameOrArticle, rev_number: int, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    pref_full_name = get_full_name(full_name_or_article)

    new_props = {}

    for entry in get_log_entries(article):
        if entry.rev_number <= rev_number:
            break

        if entry.type == ArticleLogEntry.LogEntryType.Source:
            new_props['source'] = get_previous_version(entry.meta['version_id']).source
        elif entry.type == ArticleLogEntry.LogEntryType.Title:
            new_props['title'] = entry.meta['prev_title']
        elif entry.type == ArticleLogEntry.LogEntryType.Name:
            new_props['name'] = entry.meta['prev_name']
        elif entry.type == ArticleLogEntry.LogEntryType.Tags:
            if 'added_tags' not in new_props:
                new_props['added_tags'] = []
            if 'removed_tags' not in new_props:
                new_props['removed_tags'] = []
            # logic: tags that were removed are now added
            #        tags that were added are now removed
            for tag in entry.meta['added_tags']:
                try:
                    new_props['added_tags'].remove(tag['id'])
                except ValueError:
                    pass
                new_props['removed_tags'].append(tag['id'])
            for tag in entry.meta['removed_tags']:
                try:
                    new_props['removed_tags'].remove(tag['id'])
                except ValueError:
                    pass
                new_props['added_tags'].append(tag['id'])
        elif entry.type == ArticleLogEntry.LogEntryType.New:
            # 'new' cannot be reverted. moreover, we should not reach this point at all.
            # but if we did, just stop
            break
        elif entry.type == ArticleLogEntry.LogEntryType.Parent:
            new_props['parent'] = entry.meta['prev_parent_id']
        elif entry.type == ArticleLogEntry.LogEntryType.FileAdded and 'id' in entry.meta:
            if 'files_deleted' not in new_props:
                new_props['files_deleted'] = {}
            if 'files_restored' not in new_props:
                new_props['files_restored'] = {}
            new_props['files_deleted'][entry.meta['id']] = True
            new_props['files_restored'][entry.meta['id']] = False
        elif entry.type == ArticleLogEntry.LogEntryType.FileDeleted and 'id' in entry.meta:
            if 'files_restored' not in new_props:
                new_props['files_restored'] = {}
            if 'files_deleted' not in new_props:
                new_props['files_deleted'] = {}
            new_props['files_restored'][entry.meta['id']] = True
            new_props['files_deleted'][entry.meta['id']] = False
        elif entry.type == ArticleLogEntry.LogEntryType.FileRenamed and 'id' in entry.meta:
            if 'files_renamed' not in new_props:
                new_props['files_renamed'] = {}
            new_props['files_renamed'][entry.meta['id']] = entry.meta['prev_name']
        elif entry.type == ArticleLogEntry.LogEntryType.Wikidot:
            # this is a fake revision type.
            pass
        elif entry.type == ArticleLogEntry.LogEntryType.VotesDeleted:
            new_props['votes'] = entry.meta
        elif entry.type == ArticleLogEntry.LogEntryType.Revert:
            if 'source' in entry.meta:
                new_props['source'] = get_previous_version(entry.meta['source']['version_id']).source
            if 'title' in entry.meta:
                new_props['title'] = entry.meta['title']['prev_title']
            if 'name' in entry.meta:
                new_props['name'] = entry.meta['name']['prev_name']
            if 'parent' in entry.meta:
                new_props['parent'] = entry.meta['parent']['prev_parent_id']
            if 'tags' in entry.meta:
                if 'added_tags' not in new_props:
                    new_props['added_tags'] = []
                if 'removed_tags' not in new_props:
                    new_props['removed_tags'] = []
                # logic: tags that were removed are now added
                #        tags that were added are now removed
                for tag in entry.meta['tags']['added']:
                    try:
                        new_props['added_tags'].remove(tag)
                    except ValueError:
                        pass
                    new_props['removed_tags'].append(tag)
                for tag in entry.meta['tags']['removed']:
                    try:
                        new_props['removed_tags'].remove(tag)
                    except ValueError:
                        pass
                    new_props['added_tags'].append(tag)
            if 'files' in entry.meta:
                if 'files_restored' not in new_props:
                    new_props['files_restored'] = {}
                if 'files_deleted' not in new_props:
                    new_props['files_deleted'] = {}
                if 'files_renamed' not in new_props:
                    new_props['files_renamed'] = {}
                for f in entry.meta['files']['added']:
                    new_props['files_deleted'][f['id']] = True
                    new_props['files_restored'][f['id']] = False
                for f in entry.meta['files']['deleted']:
                    new_props['files_restored'][f['id']] = True
                    new_props['files_deleted'][f['id']] = False
                for f in entry.meta['files']['renamed']:
                    new_props['files_renamed'][f['id']] = f['prev_name']
            if 'votes' in entry.meta:
                new_props['votes'] = entry.meta['votes']

    subtypes = []

    meta = {}

    files_added_meta = []
    files_deleted_meta = []
    files_renamed_meta = []

    for f_id, new_name in new_props.get('files_renamed', {}).items():
        try:
            file = File.objects.get(id=f_id)
            files_renamed_meta.append({'id': f_id, 'name': new_name, 'prev_name': file.name})
            file.name = new_name
            file.save()
        except File.DoesNotExist:
            continue

    for f_id, deleted in new_props.get('files_deleted', {}).items():
        if not deleted:
            continue
        try:
            file = File.objects.get(id=f_id)
            if not file.deleted_at:
                files_deleted_meta.append({'id': f_id, 'name': file.name})
                file.deleted_at = datetime.datetime.now()
                file.deleted_by = user
                file.save()
        except File.DoesNotExist:
            continue

    for f_id, restored in new_props.get('files_restored', {}).items():
        if not restored:
            continue
        try:
            file = File.objects.get(id=f_id)
            if file.deleted_at:
                files_added_meta.append({'id': f_id, 'name': file.name})
                file.deleted_at = None
                file.deleted_by = None
                file.save()
        except File.DoesNotExist:
            continue

    if files_added_meta or files_deleted_meta or files_renamed_meta:
        if files_added_meta:
            subtypes.append(ArticleLogEntry.LogEntryType.FileAdded)
        if files_deleted_meta:
            subtypes.append(ArticleLogEntry.LogEntryType.FileDeleted)
        if files_renamed_meta:
            subtypes.append(ArticleLogEntry.LogEntryType.FileRenamed)
        meta['files'] = {
            'added': files_added_meta,
            'deleted': files_deleted_meta,
            'renamed': files_renamed_meta
        }

    tags_added_meta = []
    tags_removed_meta = []

    tags = [x.id for x in get_tags_internal(article)]
    for tag in new_props.get('removed_tags', []):
        # safety: some outdated revisions have string tags here
        if not isinstance(tag, int):
            continue
        try:
            tags.remove(tag)
            tags_removed_meta.append(tag)
        except ValueError:
            pass
    for tag in new_props.get('added_tags', []):
        # safety: some outdated revisions have string tags here
        if not isinstance(tag, int):
            continue
        tags.append(tag)
        tags_added_meta.append(tag)
    new_tags = list(Tag.objects.filter(id__in=tags))
    set_tags_internal(article, new_tags, user, False)

    if tags_added_meta or tags_removed_meta:
        subtypes.append(ArticleLogEntry.LogEntryType.Tags)
        meta['tags'] = {
            'added': tags_added_meta,
            'removed': tags_removed_meta
        }

    if 'source' in new_props:
        subtypes.append(ArticleLogEntry.LogEntryType.Source)
        version = ArticleVersion(
            article=article,
            source=new_props['source'],
            rendered=None
        )
        version.save()
        meta['source'] = {'version_id': version.id}

    if 'title' in new_props:
        subtypes.append(ArticleLogEntry.LogEntryType.Title)
        meta['title'] = {'prev_title': article.title, 'title': new_props['title']}
        article.title = new_props['title']
        article.save()

    if 'name' in new_props:
        subtypes.append(ArticleLogEntry.LogEntryType.Name)
        meta['name'] = {'prev_name': article.name, 'name': new_props['name']}
        update_full_name(article, new_props['name'], user, False)

    if 'parent' in new_props:
        subtypes.append(ArticleLogEntry.LogEntryType.Parent)
        try:
            parent = Article.objects.get(id=new_props['parent'])
        except Article.DoesNotExist:
            parent = None
        meta['parent'] = {
            'parent': get_full_name(parent),
            'parent_id': new_props['parent'],
            'prev_parent': get_full_name(article.parent),
            'prev_parent_id': article.parent.id if article.parent else None
        }
        article.parent = parent
        article.save()

    if 'votes' in new_props:
        subtypes.append(ArticleLogEntry.LogEntryType.VotesDeleted)
        votes_meta = _get_article_votes_meta(article)
        meta['votes'] = votes_meta
        with transaction.atomic():
            Vote.objects.filter(article=article).delete()
            for vote in new_props['votes']['votes']:
                try:
                    vote_visual_group = VisualUserGroup.objects.get(id=vote['visual_group_id'])
                except VisualUserGroup.DoesNotExist:
                    vote_visual_group = None
                try:
                    vote_user = User.objects.get(id=vote['user_id'])
                except User.DoesNotExist:
                    # missing user id means we skip this vote and can't restore it.
                    continue
                vote_date = datetime.datetime.fromisoformat(vote['date']) if vote['date'] else None
                new_vote = Vote(article=article, user=vote_user, date=vote_date, rate=vote['vote'], visual_group=vote_visual_group)
                new_vote.save()
                new_vote.date = vote_date
                new_vote.save()

    meta['rev_number'] = rev_number
    meta['subtypes'] = subtypes

    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.Revert,
        meta=meta,
        comment=''
    )

    add_log_entry(article, log)
    media.symlinks_article_update(article, pref_full_name)


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


# Refreshes links based on article version.
def refresh_article_links(article_version: ArticleVersion):
    article = article_version.article
    article_name = get_full_name(article)
    # drop all links known before
    ExternalLink.objects.filter(link_from=article_name).delete()
    # parse current source
    already_added = []
    rc = renderer.RenderContext(article=article_version.article, source_article=article_version.article, path_params={}, user=None)
    linked_pages, included_pages = renderer.single_pass_fetch_backlinks(article_version.source, rc)
    for linked_page in linked_pages:
        kt = '%s:include:%s' % (article_name.lower(), linked_page.lower())
        if kt in already_added:
            continue
        already_added.append(kt)
        new_link = ExternalLink(link_from=article_name.lower(), link_type=ExternalLink.Type.Include, link_to=linked_page.lower())
        new_link.save()
    # find links
    for included_page in included_pages:
        kt = '%s:link:%s' % (article_name.lower(), included_page.lower())
        if kt in already_added:
            continue
        already_added.append(kt)
        new_link = ExternalLink(link_from=article_name.lower(), link_type=ExternalLink.Type.Link, link_to=included_page.lower())
        new_link.save()


# Updates name of article
def update_full_name(full_name_or_article: _FullNameOrArticle, new_full_name: str, user: Optional[_UserType] = None, log: bool = True):
    article = get_article(full_name_or_article)
    prev_full_name = get_full_name(full_name_or_article)

    category, name = get_name(new_full_name)
    article.category = category
    article.name = name
    article.save()

    # update links
    ExternalLink.objects.filter(link_from__iexact=new_full_name).delete()  # this should not happen, but just to be sure
    ExternalLink.objects.filter(link_from__iexact=prev_full_name).update(link_from=new_full_name)

    if log:
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.Name,
            meta={'name': new_full_name, 'prev_name': prev_full_name}
        )
        add_log_entry(article, log)

    media.symlinks_article_update(article, prev_full_name)


def _get_article_votes_meta(full_name_or_article: _FullNameOrArticle):
    article = get_article(full_name_or_article)

    # for revision logs, we store:
    # - rating mode
    # - rating
    # - vote count
    # - popularity
    # - individual votes from each user, expressed as internal DB values
    #   (user id + username + vote value)

    rating, rating_votes, popularity, rating_mode = get_rating(article)
    votes = list(Vote.objects.filter(article=article))
    votes_meta = {
        'rating_mode': str(rating_mode),
        'rating': rating,
        'votes_count': rating_votes,
        'popularity': popularity,
        'votes': []
    }
    for vote in votes:
        votes_meta['votes'].append({
            'user_id': vote.user_id,
            'vote': vote.rate,
            'visual_group_id': vote.visual_group_id,
            'date': vote.date.isoformat() if vote.date else None
        })
    return votes_meta

def delete_article_votes(full_name_or_article: _FullNameOrArticle, user: Optional[_UserType] = None, log: bool = True):
    article = get_article(full_name_or_article)

    # fetch existing votes
    votes_meta = _get_article_votes_meta(article)
    Vote.objects.filter(article=article).delete()

    if log:
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.VotesDeleted,
            meta=votes_meta
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


def delete_article(full_name_or_article: _FullNameOrArticle):
    article = get_article(full_name_or_article)
    ExternalLink.objects.filter(link_from__iexact=get_full_name(full_name_or_article)).delete()
    media.symlinks_article_delete(article)
    article.delete()
    file_storage = Path(settings.MEDIA_ROOT) / 'media' / article.media_name
    # this may have race conditions with file upload, because filesystem does not know about database transactions
    for i in range(3):
        try:
            if os.path.exists(file_storage):
                shutil.rmtree(file_storage)
                break
        except IOError:  # expected: "directory is not empty" in case someone uploads while we are deleting
            pass


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


# Get previous version of article relative to specified
def get_previous_version(version_id: int) -> Optional[ArticleVersion]:
    try:
        version = ArticleVersion.objects.get(id=version_id)
        prev_version = ArticleVersion.objects.filter(article_id=version.article_id, created_at__lt=version.created_at).order_by('-created_at')[:1]
        if not prev_version:
            return None
        return prev_version[0]
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
    return None


# Get source of article at specific revision number
def get_source_at_rev_num(full_name_or_article: _FullNameOrArticle, rev_num: int) -> Optional[str]:
    article = get_article(full_name_or_article)
    entry = get_log_entry(article, rev_num)
    if not entry:
        return None

    def get_version_from_meta(meta):
        if 'source' in meta:
            return get_version(meta['source']['version_id'])
        elif "version_id" in meta:
            return get_version(meta["version_id"])
        else:
            return None

    version = get_version_from_meta(entry.meta)
    if not version:
        log_entries = list(get_log_entries(article))
        for old_entry in log_entries[log_entries.index(entry):]:
            version = get_version_from_meta(old_entry.meta)
            if version:
                break

    if not version:
        return None

    return version.source


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
    parent_id = parent.id if parent else None
    prev_parent_id = article.parent.id if article.parent else None
    article.parent = parent
    article.save()
    log = ArticleLogEntry(
        article=article,
        user=user,
        type=ArticleLogEntry.LogEntryType.Parent,
        meta={'parent': full_name_of_parent, 'prev_parent': prev_parent, 'parent_id': parent_id, 'prev_parent_id': prev_parent_id}
    )
    add_log_entry(article, log)


# Gets all parents
def get_breadcrumbs(full_name_or_article: _FullNameOrArticle) -> Sequence[Article]:
    article = get_article(full_name_or_article)
    output = []
    breadcrumb_ids = []
    while article and article.id not in breadcrumb_ids:
        output.append(article)
        breadcrumb_ids.append(article.id)
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


def get_tag(full_name_or_tag_id: _FullNameOrTag, create: bool = False) -> Optional[Tag]:
    if full_name_or_tag_id is None:
        return None
    if type(full_name_or_tag_id) == str:
        full_name_or_tag_id = full_name_or_tag_id.lower()
        category_name, name = get_name(full_name_or_tag_id)
        if create:
            category, _ = TagsCategory.objects.get_or_create(slug=category_name)
            tag, _ = Tag.objects.get_or_create(category=category, name=name)
            return tag
        try:
            category = TagsCategory.objects.get(slug=category_name)
            return Tag.objects.get(category=category, name=name)
        except (Tag.DoesNotExist, TagsCategory.DoesNotExist):
            return None
    if not isinstance(full_name_or_tag_id, Tag):
        raise ValueError('Expected str or Tag')
    return full_name_or_tag_id


# Get tags from article
def get_tags(full_name_or_article: _FullNameOrArticle) -> Sequence[str]:
    return list(sorted([x.full_name.lower() for x in get_tags_internal(full_name_or_article)]))


def get_tags_internal(full_name_or_article: _FullNameOrArticle) -> Sequence[Tag]:
    article = get_article(full_name_or_article)
    if article:
        return article.tags.prefetch_related("category")
    return []


def get_tags_categories(full_name_or_article: _FullNameOrArticle) -> Dict[TagsCategory, Sequence[Tag]]:
    article = get_article(full_name_or_article)
    if article:
        tags = article.tags.prefetch_related("category").exclude(name__startswith="_")
        return dict(sorted({category: list(tags.filter(category=category)) for category in set(TagsCategory.objects.prefetch_related("tag_set").filter(tag__in=tags))}.items(), key=lambda x: x[0].priority if x[0].priority is not None else tags.count()))
    return {}


# Set tags for article
def set_tags(full_name_or_article: _FullNameOrArticle, tags: Sequence[Union[str]], user: Optional[_UserType] = None, log: bool = True):
    article = get_article(full_name_or_article)

    allow_creating = article.get_settings().creating_tags_allowed
    tags = list(filter(lambda x: x is not None, [get_tag(x, create=allow_creating) for x in tags if is_tag_name_allowed(x)]))

    return set_tags_internal(article, tags, user=user, log=log)


def set_tags_internal(full_name_or_article: _FullNameOrArticle, tags: Sequence[Tag], user: Optional[_UserType] = None, log: bool = True):
    article = get_article(full_name_or_article)
    article_tags = article.tags.all()

    removed_tags = []
    added_tags = []

    for tag in article_tags:
        if tag not in tags:
            article.tags.remove(tag)
            removed_tags.append({'id': tag.id, 'name': tag.full_name})

    for tag in tags:
        if tag not in article_tags:
            # possibly create the tag here
            article.tags.add(tag)
            added_tags.append({'id': tag.id, 'name': tag.full_name})

    if article.get_settings().creating_tags_allowed:
        # garbage collect tags if anything was removed
        Tag.objects.annotate(num_articles=Count('articles')).filter(num_articles=0).delete()
        TagsCategory.objects.annotate(num_tags=Count('tag')).filter(num_tags=0, slug=F('name')).delete()

    if (removed_tags or added_tags) and log:
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.Tags,
            meta={'added_tags': added_tags, 'removed_tags': removed_tags}
        )
        add_log_entry(article, log)


# Get article comment info
# This may actually create a thread if it does not exist yet
def get_comment_info(full_name_or_article: _FullNameOrArticle) -> tuple[int, int]:
    article = get_article(full_name_or_article)
    if not article:
        return 0, 0
    thread, created = ForumThread.objects.get_or_create(article=article)
    if created:
        notifications.subscribe_to_notifications(subscriber=article.author, forum_thread=thread)
    post_count = ForumPost.objects.filter(thread=thread).count()
    return thread.id, post_count


# Get article rating
def get_rating(full_name_or_article: _FullNameOrArticle) -> tuple[int | float, int, int, Settings.RatingMode]:
    article = get_article(full_name_or_article)
    if not article:
        return 0, 0, 0, Settings.RatingMode.Disabled
    obj_settings = article.get_settings()
    if obj_settings.rating_mode == Settings.RatingMode.UpDown:
        data = article.votes.aggregate(sum=Coalesce(Sum('rate'), 0, output_field=IntegerField()), count=Count('rate'), good=Count('rate', filter=Q(rate=1)))
        return data['sum'] or 0, data['count'] or 0, round((data['good'] or 0) / (data['count'] or 1) * 100), obj_settings.rating_mode
    elif obj_settings.rating_mode == Settings.RatingMode.Stars:
        data = article.votes.aggregate(avg=Coalesce(Avg('rate'), 0.0), count=Count('rate'), good=Count('rate', filter=Q(rate__gte=3)))
        return round(data['avg'], 1) or 0.0, data['count'] or 0, round((data['good'] or 0) / (data['count'] or 1) * 100), obj_settings.rating_mode
    elif obj_settings.rating_mode == Settings.RatingMode.Disabled:
        return 0, 0, 0, obj_settings.rating_mode
    else:
        raise ValueError('Unsupported rate type "%s"' % obj_settings.rating_mode)


def get_formatted_rating(full_name_or_article: _FullNameOrArticle) -> str:
    article = get_article(full_name_or_article)
    if not article:
        return '0'
    rating, votes, _, mode = get_rating(article)
    if mode == Settings.RatingMode.UpDown:
        return '%+d' % rating
    elif mode == Settings.RatingMode.Stars:
        if not votes:
            return '—'
        return '%.1f' % rating
    else:
        return '%d' % rating


class VotedTooSoonError(RuntimeError):
    def __init__(self, *args, time_left=0, time_total=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.time_left = time_left
        self.time_total = time_total


def add_vote(full_name_or_article: _FullNameOrArticle, user: _UserType, rate: int | float | None):
    article = get_article(full_name_or_article)

    old_vote_query = Vote.objects.filter(article=article, user=user)
    old_vote = old_vote_query.first()
    old_vote_query.delete()

    # temporarily disabled
    if False and not user.is_staff and not user.is_superuser and not old_vote:
        last_vote_of_this_user = Vote.objects.filter(user=user).order_by('-id').first()
        if last_vote_of_this_user and last_vote_of_this_user.date:
            time_since = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - last_vote_of_this_user.date
            time_total = datetime.timedelta(minutes=3)
            if time_since < time_total:
                time_left = time_total - time_since
                raise VotedTooSoonError('Voting too soon (at least 5 minutes between votes expected)', time_left=time_left.seconds, time_total=time_total.seconds)

    new_vote = None
    if rate is not None:
        new_vote = Vote(article=article, user=user, rate=rate, visual_group=user.visual_group)
        new_vote.save()

    OnVote(user, article, old_vote, new_vote).emit()
    


# Set article lock status
def set_lock(full_name_or_article: _FullNameOrArticle, locked: bool, user: Optional[_UserType] = None):
    article = get_article(full_name_or_article)
    article.locked = locked
    article.save()


# Get file in article
def get_file_in_article(full_name_or_article: _FullNameOrArticle, file_name: str) -> Optional[File]:
    article = get_article(full_name_or_article)
    if article is None:
        return None
    files = File.objects.filter(article=article, name__iexact=file_name, deleted_at__isnull=True)
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
        meta={'name': file.name, 'id': file.id}
    )
    add_log_entry(article, log)
    media.symlinks_article_update(article)


def get_file_space_usage() -> tuple[int, int]:
    current_files_size = File.objects.filter(deleted_at=None).aggregate(size=Sum('size')).get('size') or 0
    absolute_files_size = File.objects.aggregate(size=Sum('size')).get('size') or 0
    return current_files_size, absolute_files_size


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
        media.symlinks_article_update(article)
    else:
        file.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        file.deleted_by = user
        file.save()
        log = ArticleLogEntry(
            article=article,
            user=user,
            type=ArticleLogEntry.LogEntryType.FileDeleted,
            meta={'name': file.name, 'id': file.id}
        )
        add_log_entry(article, log)
        media.symlinks_article_update(article)


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
        meta={'name': file.name, 'id': file.id}
    )
    add_log_entry(article, log)
    media.symlinks_article_update(article)


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
            meta={'name': file.name, 'prev_name': old_name, 'id': file.id}
        )
        add_log_entry(article, log)
    media.symlinks_article_update(article)


# Check if name is allowed for creation
# Pretty much this blocks six 100% special paths, everything else is OK
def is_full_name_allowed(article_name: str) -> bool:
    article_name = article_name.lower()
    reserved = ['-', '_', 'api', 'forum', 'local--files', 'local--code', 'local--html', 'local--theme']
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


# Fetch multiple articles by names
def fetch_articles_by_names(original_names):
    names = list(dict.fromkeys([('_default:%s' % x).lower() if ':' not in x else x.lower() for x in original_names]))
    all_articles = Article.objects.annotate(
        dumb_name=Lower(Concat('category', Value(':'), 'name', output_field=TextField()))).filter(dumb_name__in=names)
    ret_map = dict()
    for article in all_articles:
        ret_map[article.dumb_name] = article
    articles_dict = dict()
    for name in original_names:
        dumb_name = ('_default:%s' % name).lower() if ':' not in name else name.lower()
        articles_dict[name] = ret_map[dumb_name]
    return articles_dict
