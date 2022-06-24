from web.controllers.articles import get_rating, Vote, has_perm
from . import ModuleError
from web.controllers import articles

from renderer.utils import render_user_to_json, render_template_from_string


def render(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    rating = get_rating(context.article)
    return render_template_from_string(
        """
        <div class="w-rate-module page-rate-widget-box" data-page-id="{{page_id}}">
        <span class="rate-points">рейтинг:&nbsp;<span class="number prw54353">{{rating}}</span></span>
        <span class="rateup btn btn-default"><a title="Мне нравится" href="#">+</a></span>
        <span class="ratedown btn btn-default"><a title="Мне не нравится" href="#">–</a></span>
        <span class="cancel btn btn-default"><a title="Отменить голос" href="#">x</a></span>
        </div>
        """,
        page_id=context.article.full_name,
        rating='%+d'%rating
    )


def allow_api():
    return True


def api_get_rating(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    return {'pageId': context.article.full_name, 'rating': articles.get_rating(context.article)}


def api_get_votes(context, _params):
    if not context.article:
        raise ModuleError('Страница не указана')
    votes = []
    for db_vote in Vote.objects.filter(article=context.article).order_by('-user__username'):
        votes.append({'user': render_user_to_json(db_vote.user), 'value': db_vote.rate})
    return {'pageId': context.article.full_name, 'votes': votes, 'rating': articles.get_rating(context.article)}


def api_rate(context, params):
    if not context.article:
        raise ModuleError('Страница не указана')

    if not has_perm(context.user, "web.can_vote_article", context.article):
        raise ModuleError('Недостаточно прав')

    if 'value' not in params:
        raise ModuleError('Не указано значение оценки')

    articles.add_vote(context.article, context.user, params['value'])

    return api_get_rating(context, params)
