from typing import dataclass_transform
from dataclasses import asdict, dataclass, is_dataclass

def drop_nones(fields_to_drop=None):
    def wrapper(cls):
        if fields_to_drop:
            def drop_none_fields(self, fields: dict):
                for field in fields_to_drop or fields:
                    if field in fields and fields[field] == None:
                        fields.pop(field)
                return fields

            cls._drop_none_fields = drop_none_fields
        return cls
    return wrapper


@dataclass_transform()
class JSONInterface:
    def __init_subclass__(cls, **kwargs):
        dataclass_params = {
            key: kwargs.pop(key)
            for key in ['init', 'repr', 'eq', 'order', 'unsafe_hash', 'frozen']
            if key in kwargs
        }
        
        cls = dataclass(**dataclass_params)(cls)

    def dump(self):
        if is_dataclass(self):
            return asdict(self)
        return {}
    
    def _drop_none_fields(self, fields):
        return fields
    