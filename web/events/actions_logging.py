from django.forms.models import model_to_dict

from modules.forumpost import OnForumDeletePost, OnForumEditPost, OnForumPinPost
from modules.forumnewpost import OnForumNewPost

from web.events import on_trigger
from web.controllers.logging import add_action_log
from web.controllers.articles import OnVote, OnCreateArticle, OnDeleteArticle, OnEditArticle, get_rating
from web.controllers.forum_reactions import OnForumReactionAdd, OnForumReactionRemove
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
        'title': e.title,
        'source': e.source
    }
    
    add_action_log(e.post.author, ActionLogEntry.ActionType.NewForumPost, meta)


@on_trigger(OnForumEditPost)
def log_forum_edit_post(e: OnForumEditPost):
    meta = {
        'author_id': e.post.author.id,
        'post': model_to_dict(e.post),
        'title': e.title,
        'prev_title': e.prev_title,
        'source': e.source,
        'prev_source': e.prev_source
    }
    
    add_action_log(e.user, ActionLogEntry.ActionType.EditForumPost, meta)


@on_trigger(OnForumDeletePost)
def log_forum_delete_post(e: OnForumDeletePost):
    meta = {
        'author_id': e.post.author.id,
        'post': model_to_dict(e.post),
        'title': e.title,
        'source': e.source
    }
    
    add_action_log(e.user, ActionLogEntry.ActionType.RemoveForumPost, meta)


@on_trigger(OnForumPinPost)
def log_forum_pin_post(e: OnForumPinPost):
    meta = {
        'author_id': e.post.author_id,
        'post': model_to_dict(e.post),
        'thread': {
            'id': e.post.thread_id,
            'name': e.post.thread.name,
        },
        'is_pinned': e.is_pinned,
        'prev_is_pinned': e.prev_is_pinned,
    }

    action_type = ActionLogEntry.ActionType.PinForumPost if e.is_pinned else ActionLogEntry.ActionType.UnpinForumPost
    add_action_log(e.user, action_type, meta)


def _forum_reaction_meta(post, reaction, target_user):
    return {
        'post': model_to_dict(post),
        'thread': {
            'id': post.thread_id,
            'name': post.thread.name,
        },
        'reaction': {
            'id': reaction.id,
            'name': reaction.name,
            'image': str(reaction.image),
        },
        'target_user': {
            'id': target_user.id,
            'username': target_user.username,
        },
    }


@on_trigger(OnForumReactionAdd)
def log_forum_reaction_add(e: OnForumReactionAdd):
    add_action_log(
        e.user,
        ActionLogEntry.ActionType.AddForumReaction,
        _forum_reaction_meta(e.post, e.reaction, e.user),
    )


@on_trigger(OnForumReactionRemove)
def log_forum_reaction_remove(e: OnForumReactionRemove):
    add_action_log(
        e.user,
        ActionLogEntry.ActionType.RemoveForumReaction,
        _forum_reaction_meta(e.post, e.reaction, e.target_user),
    )
