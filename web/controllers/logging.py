import json
from django.contrib.auth.models import AbstractUser as _UserType
from django.utils.safestring import mark_safe

from renderer import single_pass_render
from renderer.parser import RenderContext
from renderer.utils import render_template_from_string, render_user_to_html
from modules.forumthread import render_posts

from web import threadvars
from web.models.logs import ActionLogEntry
from web.models.users import User


def add_action_log(user: _UserType, type: ActionLogEntry.ActionType, meta):
    with threadvars.context():
        ActionLogEntry(
            user=user,
            stale_username=user.username,
            type=type,
            meta=meta,
            origin_ip = threadvars.get('current_client_ip')
        ).save()


def _mark_safe_all(data: dict):
    return {k: mark_safe(v) if isinstance(v, str) else v for k, v in data.items()}


def _make_post_preview(post_id, author_id, title, source):
    context = RenderContext(None, None, {}, None)
    post_info = {
        'id': post_id,
        'name':title,
        'author': render_user_to_html(User.objects.filter(id=author_id).first()),
        'content': single_pass_render(source, context, 'message'),
        'created_at': '',
        'updated_at':  '',
        'replies': [],
        'rendered_replies': False,
        'options_config': json.dumps({
            'hasRevisions': False,
            'canReply': False,
            'canEdit': False,
            'canDelete': False,
        })
    }
    return render_posts([post_info])

def _render_post_edit_preview(m):
    body = render_template_from_string(
        """
        <div class="w-tabview">
            <ul class="yui-nav post-versions">
                <li class=""><a href="javascript:;">Старая</a></li>
                |
                <li class="selected" title="active"><a href="javascript:;">Новая</a></li>
            </ul>
            <div class="yui-content">
                <div class="w-tabview-tab" style="display: none;">
                    {{prev_post}}
                </div>
                <div class="w-tabview-tab" style="display: block;">
                    {{post}}
                </div>
            </div>
        </div>
        """,
        prev_post=_make_post_preview(m['post']['id'], m['post']['author'], m['title'], m['prev_source']),
        post=_make_post_preview(m['post']['id'], m['post']['author'], m['title'], m['source'])
    )
    return body


def get_action_log_entry_description(log_entry: ActionLogEntry):
    ActionType = ActionLogEntry.ActionType
    m = log_entry.meta
    try:
        match log_entry.type:
            case ActionType.Vote:
                m = _mark_safe_all(m)
                if m['is_new']:
                    return f"На страницу {m['article']} добавлена оценка {m['new_vote']}"
                elif m['is_remove']:
                    return f"Со страницы {m['article']} удалена оценка {m['old_vote']}"
                elif m['is_change']:
                    return f"Оценка на странице {m['article']} изменена с {m['old_vote']} на {m['new_vote']}"
            case ActionType.NewArticle:
                m = _mark_safe_all(m)
                return f"Создана новая страница: {m['article']}"
            case ActionType.RemoveArticle:
                m = _mark_safe_all(m)
                return f"Страница: {m['article']}, рейтинг на момент удаления: {m['rating']}, голосов: {m['votes']}, популярность: {m['popularity']}"
            case ActionType.EditArticle:
                m = _mark_safe_all(m)
                msg = [f"Страница: {m['article']}, ревизия: {m['rev_number']}"]
                meta = m['log_entry_meta']
                match m['edit_type']:
                    case 'tags':
                        added_tags = meta['added_tags']
                        removed_tags = meta['removed_tags']
                        if added_tags:
                            msg.append(f"добавлены теги: {', '.join([t['name'] for t in added_tags])}")
                        if removed_tags:
                            msg.append(f"удалены теги: {', '.join([t['name'] for t in removed_tags])}")
                    case 'title':
                        msg.append(f"заголовок изменен c {meta['prev_title']} на {meta['title']}")
                    case 'name':
                        msg.append(f"адрес изменен c {meta['prev_name']} на {meta['name']}")
                    case 'votes_deleted':
                        msg.append(f"рейтинг сброшен")
                    case _:
                        msg.append(f"тип правки: {m['edit_type']}")
                if m['comment']:
                    msg.append(f"комментарий: {m['comment']}")
                return ', '.join(msg)
            case ActionType.NewForumPost:
                return _make_post_preview(m['post']['id'], m['post']['author'], m['title'], m['source'])
            case ActionType.EditForumPost:
                return _render_post_edit_preview(m)
            case ActionType.RemoveForumPost:
                return _make_post_preview(m['post']['id'], m['post']['author'], m['title'], m['source'])
            case _:
                return None
    except:
        return f'Ошибка обработки лога №{log_entry.id}'