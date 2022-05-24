import pkgutil
import sys
from django.utils import html


_all_modules = {}
_initialized = False


def get_all_modules():
    global _initialized, _all_modules
    if _initialized:
        return _all_modules
    package = sys.modules[__name__]
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        if ispkg:
            continue
        try:
            m = importer.find_module(modname).load_module(modname)
        except:
            continue
        if 'render' not in m.__dict__:
            continue
        if not callable(m.render):
            continue
        _all_modules[modname.lower()] = m
    _initialized = True
    return _all_modules


def module_has_content(name):
    name = name.lower()
    modules = get_all_modules()
    if name not in modules:
        return False
    m = modules[name]
    if 'has_content' not in m.__dict__ or not callable(m.has_content):
        return False
    return m.has_content()


def render_module(name, context, params, content=None):
    name = name.lower()
    modules = get_all_modules()
    if name not in modules:
        #return '<div class="error-block"><p>Модуль \'%s\' не существует</p></div>' % html.escape(name)
        return ''
    try:
        if module_has_content(name):
            return modules[name].render(context, params, content)
        else:
            return modules[name].render(context, params)
    except:
        return '<div class="error-block"><p>Ошибка обработки модуля \'%s\'</p></div>' % html.escape(name)
