from django.contrib.auth.models import AnonymousUser

from web.controllers.articles import get_rating, Vote
from web.models.settings import Settings
from . import ModuleError
from web.controllers import articles, permissions

from renderer.utils import render_user_to_json, render_template_from_string


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


def allow_api():
    return True


def api_get_rating(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    rating, votes, popularity, mode = articles.get_rating(context.article)
    return {'pageId': context.article.full_name, 'rating': rating, 'voteCount': votes, 'popularity': popularity, 'ratingMode': mode}


def api_get_votes(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    votes = []
    rating, _, popularity, mode = articles.get_rating(context.article)
    for db_vote in Vote.objects.filter(article=context.article).order_by('-date', '-user__username'):
        rendered_vote = {'user': render_user_to_json(db_vote.user), 'value': db_vote.rate}
        if context.user.is_staff or context.user.is_superuser:
            rendered_vote['date'] = db_vote.date.isoformat() if db_vote.date else None
        votes.append(rendered_vote)
    return {'pageId': context.article.full_name, 'votes': votes, 'rating': rating, 'popularity': popularity, 'mode': mode}


def api_rate(context, params):
    if not context.article:
        raise ModuleError('Страница не указана')

    if not permissions.check(context.user, "rate", context.article):
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
            if value < 0 or value > 5:
                raise ModuleError('Некорректная оценка %s' % str(value))

    articles.add_vote(context.article, context.user, value)

    return api_get_rating(context, params)
