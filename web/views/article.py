from django.http import HttpResponse
from django.template import loader

from web.controllers import articles

from renderer import single_pass_render
from renderer.parser import RenderContext

import json


def index(request, article_name='main'):
    template = loader.get_template('page.html')

    # get article itself
    title = None
    article = articles.get_article(article_name)
    nav_top_article = articles.get_article('nav:top')
    nav_side_article = articles.get_article('nav:side')

    if article is not None:
        content = single_pass_render(articles.get_latest_source(article), RenderContext(article, article))
        if article_name != 'main':
            title = article.title
        status = 200
    else:
        template_404 = loader.get_template('page_404.html')
        context = {'page_id': article_name, 'allow_create': articles.is_full_name_allowed(article_name)}
        content = template_404.render(context, request)
        status = 404

    nav_top = single_pass_render(articles.get_latest_source(nav_top_article), RenderContext(article, nav_top_article)) if nav_top_article else ''
    nav_side = single_pass_render(articles.get_latest_source(nav_side_article), RenderContext(article, nav_side_article)) if nav_side_article else ''

    options_config = {
        'optionsEnabled': True,
        'editable': True,
        'pageId': article_name
    }

    context = {
        'content': content,
        'nav_top': nav_top,
        'nav_side': nav_side,
        'title': title,
        'options_config': json.dumps(options_config)
    }

    return HttpResponse(template.render(context, request), status=status)
