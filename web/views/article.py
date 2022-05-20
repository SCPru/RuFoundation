from django.http import HttpResponse
from django.template import loader
from django.conf import settings

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

    nav_top = single_pass_render(articles.get_latest_source(nav_top_article), RenderContext(article, nav_top_article)) if nav_top_article else ''
    nav_side = single_pass_render(articles.get_latest_source(nav_side_article), RenderContext(article, nav_side_article)) if nav_side_article else ''

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

    options_config = {
        'optionsEnabled': True,
        'editable': settings.ANONYMOUS_EDITING_ENABLED,
        'pageId': article_name
    }

    context = {
        'site_name': settings.WEBSITE_NAME,
        'site_headline': settings.WEBSITE_HEADLINE,
        'site_title': title or settings.WEBSITE_NAME,
        'content': content,
        'nav_top': nav_top,
        'nav_side': nav_side,
        'title': title,
        'options_config': json.dumps(options_config)
    }

    return HttpResponse(template.render(context, request), status=status)
