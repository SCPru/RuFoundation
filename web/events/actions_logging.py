from django.forms.models import model_to_dict

from modules.forumpost import OnForumDeletePost, OnForumEditPost
from modules.forumnewpost import OnForumNewPost

from web.events import on_trigger
from web.controllers.logging import add_action_log
from web.controllers.articles import OnVote, OnCreateArticle, OnDeleteArticle, OnEditArticle, get_rating
from web.models.logs import ActionLogEntry


@on_trigger(OnVote)
def log_vote(e: OnVote):    
    meta = {
        'article': str(e.article),
        'old_vote': e.old_vote.rate if e.old_vote else None,
        'new_vote': e.new_vote.rate if e.new_vote else None,
        'is_new': e.is_new,
        'is_change': e.is_change,
        'is_remove': e.is_remove
    }
    
    add_action_log(e.user,  ActionLogEntry.ActionType.Vote, meta)


@on_trigger(OnCreateArticle)
def log_create_article(e: OnCreateArticle):
    meta = {
        'article': str(e.article)
    }
    
    add_action_log(e.user, ActionLogEntry.ActionType.NewArticle, meta)


@on_trigger(OnDeleteArticle)
def log_delete_article(e: OnDeleteArticle):
    rating, votes, popularity, _ = get_rating(e.article)
    meta = {
        'article': str(e.article),
        'rating': rating,
        'votes': votes,
        'popularity': popularity
    }
    
    add_action_log(e.user, ActionLogEntry.ActionType.RemoveArticle, meta)


@on_trigger(OnEditArticle)
def log_edit_article(e: OnEditArticle):
    if e.is_new:
        return
    
    meta = {
        'article': str(e.article),
        'comment': e.log_entry.comment,
        'edit_type': e.log_entry.type,
        'rev_number': e.log_entry.rev_number,
        'log_entry_meta': e.log_entry.meta
    }
    
    add_action_log(e.user, ActionLogEntry.ActionType.EditArticle, meta)


@on_trigger(OnForumNewPost)
def log_forum_new_post(e: OnForumNewPost):
    meta = {
        'author_id': e.post.author.id,
        'post': model_to_dict(e.post),
        'title': e.post.name,
        'source': e.source
    }
    
    add_action_log(e.post.author, ActionLogEntry.ActionType.NewForumPost, meta)


@on_trigger(OnForumEditPost)
def log_forum_edit_post(e: OnForumEditPost):
    meta = {
        'author_id': e.post.author.id,
        'post': model_to_dict(e.post),
        'title': e.title,
        'source': e.source,
        'prev_source': e.prev_source
    }
    
    add_action_log(e.post.author, ActionLogEntry.ActionType.EditForumPost, meta)


@on_trigger(OnForumDeletePost)
def log_forum_delete_post(e: OnForumDeletePost):
    meta = {
        'author_id': e.post.author.id,
        'post': model_to_dict(e.post),
        'title': e.title,
        'source': e.source
    }
    
    add_action_log(e.post.author, ActionLogEntry.ActionType.RemoveForumPost, meta)