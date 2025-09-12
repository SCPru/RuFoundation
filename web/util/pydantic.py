from pydantic import BaseModel


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


class JSONInterface(BaseModel):
    def model_dump(self, *args, **kwargs):
        dump = super().model_dump(*args, **kwargs)
        return self._drop_none_fields(dump)
    
    def _drop_none_fields(self, fields):
        return fields
    