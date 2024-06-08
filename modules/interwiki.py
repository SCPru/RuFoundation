import json
from langcodes import Language
import logging

from web.controllers import articles
import renderer
from renderer.templates import apply_template
from renderer.utils import render_template_from_string
from web.models.sites import get_current_site
from shared_data import interwiki_batcher


def has_content():
    return True


def render(context, params, content=''):
    # params:
    # - article: article name
    # - prependline: FTML to render before everything
    # - appendline: FTML to render after everything
    # - language: language to name languages in. default - native
    # - omitlanguage: language to ignore in the response
    # - empty: FTML to render if there is no content
    # - loading: FTML to render while loading
    # content:
    # will be rendered for each translation. available variables:
    # - %%url%%
    # - %%language%%
    # - %%language_code%%

    loading_source = params.get('loading', '')
    loading_rendered = renderer.single_pass_render(loading_source, context=context) if loading_source else None

    return render_template_from_string(
        """
        <div class="w-interwiki" data-interwiki-configuration="{{params}}">{{loading_rendered|safe}}</div>
        """,
        params=json.dumps({
            'params': params,
            'content': content,
            'loading': loading_rendered,
            'pageId': context.article.full_name if context and context.article else None
        }),
        loading_rendered=loading_rendered
    )


def allow_api():
    return True


def translate_language(language, in_language=''):
    if not language:
        return '???'
    try:
        return Language.get(language).display_name(in_language or language).title()
    except (TypeError, NameError, ValueError):
        return language


def api_render_for_languages(context, params):
    site = get_current_site(required=True)
    article_name = params.get('article', '')
    domain_to_check = 'http://%s' % site.domain
    url_to_check = '%s/%s' % (domain_to_check, articles.normalize_article_name(article_name))

    translations = interwiki_batcher.query_interwiki(url_to_check)

    try:
        all_urls = set()
        for page in translations['page']['translations']:
            all_urls.add(page['url'])
        translation_of = translations['page'].get('translationOf')
        if translation_of:
            all_urls.add(translation_of['url'])
            for page in translation_of['translations']:
                all_urls.add(page['url'])
        all_urls = [x for x in all_urls if x]
    except (KeyError, TypeError, ValueError):
        logging.error('InterWiki: Failed to load languages from response %s' % json.dumps(translations))
        return {'result': ''}

    try:
        language_mapping = translations['sites']
    except (KeyError, TypeError, ValueError):
        logging.error('InterWiki: Failed to load sites from response %s' % json.dumps(translations))
        return {'result': ''}

    uncertain_languages = set([x['language'] for x in language_mapping if len([y for y in language_mapping if y['language'] == x['language'] and y['type'] == x['type']]) > 1])

    rendered_articles = []
    for url in all_urls:
        if url == url_to_check or url.startswith(domain_to_check):
            continue
        language_name = '???'
        language_code = '??'
        language = [x for x in language_mapping if url.startswith(x['url'])]
        if language:
            language = language[0]
            language_code = language['language']
            if language['language'] not in uncertain_languages:
                language_name = translate_language(language['language'], params.get('language', ''))
            else:
                language_name = language['displayName']
                if ' - ' in language_name:
                    language_name = language_name.split(' - ', 1)[1]
        if language_code.lower() == params.get('omitlanguage', ''):
            continue
        rendered_articles.append({
            'url': url,
            'language': language_name,
            'language_code': language_code
        })
    rendered_articles = sorted(rendered_articles, key=lambda x: x['language'])

    if rendered_articles:
        source = params.get('prependline', '')+'\n'
        for article in rendered_articles:
            source += apply_template(params.get('content', '')+'\n', article)
        source += params.get('appendline', '')
    elif params.get('empty', ''):
        source = params.get('empty', '')
    else:
        source = ''

    return {
        'result': renderer.single_pass_render(source, context=context)
    }
