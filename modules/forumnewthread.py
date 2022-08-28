from modules import ModuleError
from renderer import RenderContext, render_template_from_string
import json

from renderer.utils import render_user_to_json
from web.controllers import articles
from web.models.forum import ForumCategory, ForumThread, ForumPost


def has_content():
    return False


def render(context: RenderContext, params):
    context.title = 'Создать тему'

    c = context.path_params.get('c')
    try:
        c = int(c)
        category = ForumCategory.objects.filter(id=c)
        category = category[0] if category else None
    except:
        category = None

    if category is None:
        context.status = 404
        raise ModuleError('Категория "%s" не найдена' % c)

    num_threads = ForumThread.objects.filter(category=category).count()
    num_posts = ForumPost.objects.filter(thread__category=category).count()

    canonical_url = '/forum/c-%d/%s' % (category.id, articles.normalize_article_name(category.name))

    editor_options = {
        'categoryId': category.id,
        'user': render_user_to_json(context.user),
        'cancelUrl': canonical_url
    }

    return render_template_from_string(
        """
        <div class="forum-new-thread-box">
            <div class="forum-breadcrumbs">
                <a href="/forum/start">Форум</a>
                &raquo;
                <a href="{{ canonical_url }}">{{ breadcrumb }}</a>
                &raquo;
                Создать тему
            </div>
            <div class="description well">
                <div class="statistics">
                    Число тем: {{ num_threads }}
                    <br>
                    Число сообщений: {{ num_posts }}
                </div>
                {{ description }}
            </div>
        </div>
        <!-- lets fucking hope no one attempted to style the forum page -->
        <div class="w-forum-post-editor" data-options="{{ editor_options }}"></div>
        """,
        breadcrumb='%s / %s' % (category.section.name, category.name),
        description=category.description,
        num_threads=num_threads,
        num_posts=num_posts,
        canonical_url=canonical_url,
        editor_options=json.dumps(editor_options)
    )
