import copy

from django.contrib.auth.models import Group
from django.template import Context
from jazzmin.templatetags import jazzmin
from jazzmin.settings import get_settings

import system
import web

register = jazzmin.register


# This fixes categories in side menu
@register.simple_tag(takes_context=True)
def get_side_menu(context: Context, using: str = "available_apps") -> list[dict]:
    available_apps = copy.deepcopy(context.get(using, []))

    options = get_settings()

    structure = (
        ('Пользователи и группы', (
            {'model': Group},
            {'model': system.models.User},
        )),
        ('Статьи', (
            {'model': web.models.sites.Site},
            {'model': web.models.articles.Category},
            {'model': web.models.articles.TagsCategory},
            {'model': web.models.articles.Tag},
        )),
        ('Форум', (
            {'model': web.models.forum.ForumSection},
            {'model': web.models.forum.ForumCategory},
        ))
    )

    app_label_by_model = dict()
    model_meta_by_model = dict()

    # I'm iterating the original array because it's been permission-filtered already
    for app in available_apps:
        for model in app.get("models", []):
            model_meta_by_model[model["model"]] = model
            app_label_by_model[model["model"]] = app["app_label"].lower()

    print(repr(model_meta_by_model))

    menu = []

    for section in structure:
        print(repr(section))
        app = dict()
        app["icon"] = options["default_icon_parents"]
        app["name"] = section[0]
        app["models"] = []
        for model in section[1]:
            app_label = app_label_by_model[model["model"]]
            model = model_meta_by_model[model["model"]]
            if not model:
                continue
            print(repr(model))
            model_str = "{app_label}.{model}".format(app_label=app_label, model=model["object_name"]).lower()
            if model_str in options.get("hide_models", []):
                continue
            item = copy.deepcopy(model)
            item["url"] = item["admin_url"]
            item["model_str"] = model_str
            item["icon"] = options["icons"].get(model_str, options["default_icon_children"])
            app["models"].append(item)
        if not app["models"]:
            continue
        menu.append(app)

    return menu
