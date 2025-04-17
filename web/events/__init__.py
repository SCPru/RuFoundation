import re
import sys
import pkgutil
import logging
from importlib.util import module_from_spec
from dataclasses import dataclass


_event_handlers: dict[str, list] = {}


def camel_to_snake(camel_str):
    # Wierd thing to translate camel-case to snake-case like this:
    #     TestString -> test_string
    #     AnotherABCTestString -> another_abc_test_string
    return re.sub(r'(?<!^)([A-Z][a-z]|(?<=[a-z])[A-Z])', r'_\1', camel_str).lower()


class EventBase:
    event_type = None

    def __init_subclass__(cls, **kwargs):
        event_type = kwargs.pop('name', None)
        is_abstract = kwargs.pop('is_abstract', False)

        dataclass_params = {
            key: kwargs.pop(key)
            for key in ['init', 'repr', 'eq', 'order', 'unsafe_hash', 'frozen']
            if key in kwargs
        }
        
        cls = dataclass(**dataclass_params)(cls)
        
        if not is_abstract and cls.event_type is None:
            cls.event_type = event_type or camel_to_snake(cls.__name__)


    def emit(self):
        if self.event_type is None:
            raise TypeError(f'Event type is not specified for {self}.')
        emit_event(self)


def on_trigger(event: EventBase | str):
    def decorator(func):
        if isinstance(event, str):
            event_type = event
        elif issubclass(event, EventBase):
            event_type = event.event_type
        else:
            raise ValueError('Event must be str or derived from EventBase.')
        
        if event_type not in _event_handlers:
            _event_handlers[event_type] = []
        _event_handlers[event_type].append(func)

        return func
    
    return decorator


def emit_event(event: EventBase):
    handlers = _event_handlers.get(event.event_type, [])
    
    for handler in handlers:
        handler(event)


def preload_events():
    package = sys.modules[__name__]
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        try:
            spec = importer.find_spec(modname)
            m = module_from_spec(spec)
            spec.loader.exec_module(m)
            logging.info('Loaded events collection \'%s\'', modname.lower())
        except:
            logging.error('Failed to load events collection \'%s\':', modname.lower(), exc_info=True)
            continue