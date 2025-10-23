import urllib

from django.http import HttpRequest, HttpResponse

from . import APIView, APIError, takes_json

from renderer import single_pass_render
from renderer.parser import RenderContext

from web.controllers import articles

from web.views.article import ArticleView
from renderer.templates import apply_template
from modules.listpages import page_to_listpages_vars, get_page_vars
from ...models import get_current_site


class PreviewView(APIView):
    def _validate_preview_data(self):
        if not self.json_input:
            raise APIError('Некорректный запрос', 400)
        if 'pageId' not in self.json_input or not self.json_input['pageId'] or not articles.is_full_name_allowed(self.json_input['pageId']):
            raise APIError('Некорректный ID страницы', 400)
        if 'source' not in self.json_input:
            raise APIError('Отсутствует исходный код страницы', 400)

    @takes_json
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        data = self.json_input
        self._validate_preview_data()
        # find page
        article = articles.get_article(data['pageId'])
        path_params = data['pathParams'] if 'pathParams' in data else {}
        title = data['title'] if 'title' in data else ''
        source = data['source']

        template_page_vars = get_page_vars(article)
        template_page_vars['content'] = source

        template_source = '%%content%%'

        if article is not None and article.name != '_template':
            template = articles.get_article('%s:_template' % article.category)
            if template:
                template_source = articles.get_latest_source(template)

        site = get_current_site()
        encoded_params = ''
        for param in path_params:
            encoded_params += '/%s' % param
            if path_params[param] is not None:
                encoded_params += '/%s' % urllib.parse.quote(path_params[param], safe='')
        canonical_url = '//%s/%s%s' % (site.domain, article.full_name if article else data['pageId'], encoded_params)

        source = page_to_listpages_vars(article, template_source, index=1, total=1, page_vars=template_page_vars)
        source = apply_template(source, lambda param: ArticleView.get_this_page_params(path_params, param, {'canonical_url': canonical_url}))
        context = RenderContext(article, article, path_params, self.request.user)
        content = single_pass_render(source, context)
        return self.render_json(200, {'title': title, 'content': content, 'style': context.computed_style})
