from typing import dataclass_transform
from dataclasses import asdict, dataclass, is_dataclass


def drop_nones(fields_to_drop=None):
    def wrapper(cls):
        if fields_to_drop:
            old_data_processor = cls._process_result_data
            def drop_none_fields(self, data: dict):
                data = old_data_processor(self, data)
                all_data_fields = list(data)
                for field in fields_to_drop or all_data_fields:
                    if data.get(field) == None:
                        data.pop(field)
                return data

            cls._process_result_data = drop_none_fields
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
            return self._process_result_data(asdict(self))
        return {}
    
    def _process_result_data(self, data: dict):
        return data