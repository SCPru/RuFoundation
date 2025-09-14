import re
from contextlib import contextmanager

from django.db import transaction
from django.db.transaction import get_connection


@contextmanager
def lock_table(model):
    with transaction.atomic():
        cursor = get_connection().cursor()
        cursor.execute(f'LOCK TABLE {model._meta.db_table}')
        try:
            yield
        finally:
            cursor.close()


def camel_to_snake(camel_str):
    # Wierd thing to translate camel-case to snake-case like this:
    #     TestString -> test_string
    #     AnotherABCTestString -> another_abc_test_string
    return re.sub(r'(?<!^)([A-Z][a-z]|(?<=[a-z])[A-Z])', r'_\1', camel_str).lower()


def check_function_exists_and_callable(o, func):
    return func in o.__dict__ and callable(o.__dict__[func])
