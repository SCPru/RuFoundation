from django.http import HttpResponse
from django.template import loader

from web.controllers import articles

from renderer import single_pass_render


def index(request, article_name='main'):
    template = loader.get_template('page.html')

    # get article itself
    article = articles.get_article(article_name)

    content = single_pass_render(articles.get_latest_source(article), article)
    nav_top = single_pass_render(articles.get_latest_source('nav:top'), article)
    nav_side = single_pass_render(articles.get_latest_source('nav:side'), article)

    context = {
        'content': content,
        'nav_top': nav_top,
        'nav_side': nav_side
    }

    return HttpResponse(template.render(context, request))
