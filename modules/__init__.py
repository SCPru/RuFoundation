import pkgutil
import sys
import logging
from types import ModuleType

from django.db import transaction

_all_modules = {}
_initialized = False


class ModuleError(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = message


def check_function_exists_and_callable(m, func):
    return func in m.__dict__ and callable(m.__dict__[func])


def get_all_modules():
    global _initialized, _all_modules
    if _initialized:
        return _all_modules
    package = sys.modules[__name__]
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        try:
            fullname = 'modules.%s' % modname
            if fullname in sys.modules:
                m = sys.modules[fullname]
            else:
                m = importer.find_module(fullname).load_module(fullname)
        except:
            logging.error('Failed to load module \'%s\':', modname.lower(), exc_info=True)
            continue
        if not check_function_exists_and_callable(m, 'render') and not check_function_exists_and_callable(m, 'allow_api'):
            continue
        _all_modules[modname.lower()] = m
    _initialized = True
    return _all_modules


def get_module(name_or_module) -> any:
    if type(name_or_module) == str:
        name = name_or_module.lower()
        modules = get_all_modules()
        return modules.get(name, None)
    if not isinstance(name_or_module, ModuleType):
        raise ValueError('Expected str or module')
    return name_or_module


def module_has_content(name_or_module):
    m = get_module(name_or_module)
    if m is None:
        return False
    if 'has_content' not in m.__dict__ or not callable(m.__dict__['has_content']):
        return False
    return m.__dict__['has_content']()


def module_allows_api(name_or_module):
    m = get_module(name_or_module)
    if m is None:
        return False
    if 'allow_api' not in m.__dict__ or not callable(m.__dict__['allow_api']):
        return False
    return m.__dict__['allow_api']()


@transaction.atomic
def render_module(name, context, params, content=None):
    if context and context.path_params.get('nomodule', 'false') == 'true':
        raise ModuleError('Обработка модулей отключена')
    m = get_module(name)
    if m is None:
        raise ModuleError('Модуль \'%s\' не существует' % name)
    try:
        render = m.__dict__.get('render', None)
        if render is None:
            raise ModuleError('Модуль \'%s\' не поддерживает использование на странице')
        if module_has_content(m):
            return render(context, params, content)
        else:
            return render(context, params)
    except ModuleError as e:
        raise
    except:
        logging.error('Module failed: %s, Params = %s, Path = %s, Error:', name, params, context.path_params if context else None, exc_info=True)
        raise ModuleError('Ошибка обработки модуля \'%s\'' % name)


@transaction.atomic
def handle_api(name, method, context, params):
    m = get_module(name)
    if m is None:
        raise ModuleError('Модуль \'%s\' не существует' % name)
    try:
        if module_allows_api(m):
            api_method = 'api_%s' % method
            if api_method not in m.__dict__ or not callable(m.__dict__[api_method]):
                raise ModuleError('Некорректный метод для модуля \'%s\'')
            return m.__dict__[api_method](context, params)
        else:
            raise ModuleError('Модуль \'%s\' не поддерживает API')
    except ModuleError:
        raise
    except:
        logging.error('Module failed: %s, API = %s, Params = %s, Path = %s, Error:', name, method, params, context.path_params if context else None, exc_info=True)
        raise ModuleError('Ошибка обработки модуля \'%s\'' % name)
