from django.contrib.auth.models import AnonymousUser

from renderer.utils import UserJSON, render_user_to_json, render_template_from_string

from web.controllers.articles import get_rating, Vote
from web.models.settings import Settings
from web.controllers import articles
from web.util.pydantic import JSONInterface, drop_nones

from . import ModuleError
from ._csrf_protection import csrf_safe_method


def allow_api():
    return True


def render(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    rating, votes, popularity, mode = get_rating(context.article)

    if mode == Settings.RatingMode.UpDown:
        return render_template_from_string(
            ''.join([
                '<div class="w-rate-module page-rate-widget-box" data-page-id="{{page_id}}">',
                '<span class="rate-points">рейтинг:&nbsp;<span class="number prw54353">{{rating}}</span></span>',
                '<span class="rateup btn btn-default"><a title="Мне нравится" href="#">+</a></span>',
                '<span class="ratedown btn btn-default"><a title="Мне не нравится" href="#">–</a></span>',
                '<span class="cancel btn btn-default"><a title="Отменить голос" href="#">x</a></span>',
                '</div>'
            ]),
            page_id=context.article.full_name,
            rating='%+d' % rating
        )
    elif mode == Settings.RatingMode.Stars:
        return render_template_from_string(
            ''.join([
                '<div class="w-stars-rate-module" data-page-id="{{page_id}}">',
                '<div class="w-stars-rate-rating">рейтинг:&nbsp;<span class="w-stars-rate-number">{{rating}}</span></div>',
                '<div class="w-stars-rate-control">',
                '<div class="w-stars-rate-stars-wrapper"><div class="w-stars-rate-stars-view" style="width: {{rating_percentage}}%; --rated-var: {{rated}}"></div></div>',
                '<div class="w-stars-rate-cancel"></div>'
                '</div>',
                '<div class="w-stars-rate-votes"><span class="w-stars-rate-number" title="Количество голосов">{{votes}}</span>/<span class="w-stars-rate-popularity" title="Популярность (процент голосов 3.0 и выше)">{{popularity}}</span>%</div>',
                '</div>'
            ]),
            page_id=context.article.full_name,
            rating=('%.1f' % rating) if votes else '—',
            rating_percentage='%d' % (rating * 20),
            votes='%d' % votes,
            popularity='%d' % popularity,
            rated="#f0ac00" if context.user and not isinstance(context.user, AnonymousUser) and Vote.objects.filter(article=context.article, user=context.user) else '#4e6b6b'

        )
    else:
        return ''


@csrf_safe_method
def api_get_rating(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    rating, votes, popularity, mode = articles.get_rating(context.article)
    return {'pageId': context.article.full_name, 'rating': rating, 'voteCount': votes, 'popularity': popularity, 'ratingMode': mode}


@drop_nones(['date'])
class RenderedVoteJSON(JSONInterface):
    user: UserJSON
    value: float
    visualGroup: str | None=None
    visualGroupIndex: int | None=None
    date: str | None=None


@csrf_safe_method
def api_get_votes(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    votes = []
    rating, _, popularity, mode = articles.get_rating(context.article)
    can_view_votes_timestamp = context.user.has_perm('roles.view_votes_timestamp')
    for db_vote in Vote.objects.filter(article=context.article).order_by('-date', '-user__username'):
        rendered_vote = RenderedVoteJSON(
            user=render_user_to_json(db_vote.user),
            value=db_vote.rate,
            visualGroup=(db_vote.role.votes_title or db_vote.role.name or db_vote.role.slug) if db_vote.role else None,
            visualGroupIndex=db_vote.role.index if db_vote.role else None
        )
        if can_view_votes_timestamp:
            rendered_vote.date = db_vote.date.isoformat() if db_vote.date else None
        votes.append(rendered_vote)
    return {'pageId': context.article.full_name, 'votes': votes, 'rating': rating, 'popularity': popularity, 'mode': mode}


def pluralize_russian(number, base):
    if number % 10 in (2, 3, 4):
        return f'{number} {base}ы'
    if number % 10 in (5, 6, 7, 8, 9, 0):
        return f'{number} {base}'
    if number % 10 in (1,):
        return f'{number} {base}у'


def format_time(seconds):
    t_minutes = int(seconds / 60)
    t_seconds = int(seconds % 60)
    s = ''
    if t_seconds or not t_minutes:
        s = pluralize_russian(t_seconds, 'секунд')
    if t_minutes:
        s = pluralize_russian(t_minutes, 'минут') + ' ' + s
    return s


def api_rate(context, params):
    if not context.article:
        raise ModuleError('Страница не указана')

    if not context.user.has_perm('roles.rate_articles', context.article):
        raise ModuleError('Недостаточно прав')

    if 'value' not in params:
        raise ModuleError('Не указано значение оценки')

    value = params['value']

    if value is not None:
        obj_settings = context.article.get_settings()
        if obj_settings.rating_mode == Settings.RatingMode.UpDown:
            if value not in [-1, 0, 1]:
                raise ModuleError('Некорректная оценка %s' % str(value))
        elif obj_settings.rating_mode == Settings.RatingMode.Stars:
            if value < 0 or value > 5 or value % 0.5 != 0:
                raise ModuleError('Некорректная оценка %s' % str(value))

    try:
        articles.add_vote(context.article, context.user, value)
    except articles.VotedTooSoonError as e:
        raise ModuleError(f'Вы уже голосовали за другую статью менее {format_time(e.time_total)} назад. Попробуйте снова через {format_time(e.time_left)}. Вы можете воспользоваться оставшимся временем, чтобы получше ознакомиться со статьёй, которую оцениваете.')

    return api_get_rating(context, params)
