from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.conf import settings

from web.controllers import articles

from renderer import single_pass_render
from renderer.parser import RenderContext

import json


def index(request, path):
    path = path.split('/')
    article_name = path[0]
    if not article_name:
        article_name = 'main'

    path_params = {}
    path = path[1:]
    i = 0
    while i < len(path):
        key = path[i]
        value = path[i+1] if i+1 < len(path) else None
        if key or value:
            path_params[key.lower()] = value
        i += 2

    template = loader.get_template('page.html')

    # get article itself
    title = None
    article = articles.get_article(article_name)
    nav_top_article = articles.get_article('nav:top')
    nav_side_article = articles.get_article('nav:side')

    nav_top = single_pass_render(articles.get_latest_source(nav_top_article), RenderContext(article, nav_top_article, path_params)) if nav_top_article else ''
    nav_side = single_pass_render(articles.get_latest_source(nav_side_article), RenderContext(article, nav_side_article, path_params)) if nav_side_article else ''

    if article is not None:
        context = RenderContext(article, article, path_params)
        content = single_pass_render(articles.get_latest_source(article), context)
        if context.redirect_to:
            return HttpResponseRedirect(context.redirect_to)
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
