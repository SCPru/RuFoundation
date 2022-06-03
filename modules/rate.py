from web.controllers.articles import get_rating


def render(context, params):
    rating = get_rating(context.article)
    code = '<div class="w-rate-module page-rate-widget-box"><span class="rate-points">рейтинг:&nbsp;'
    code += f'<span class="number prw54353">{f"+{rating}" if rating > 0 else rating}</span></span>'
    code += '<span class="rateup btn btn-default"><a title="Мне нравится" href="#">+</a></span><span class="ratedown btn btn-default"><a title="Мне не нравится" href="#">–</a></span><span class="cancel btn btn-default"><a title="Отменить голос" href="#">x</a></span></div>'
    return code
