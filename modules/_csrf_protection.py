def csrf_safe_method(func):
    setattr(func, 'is_csrf_safe', True)
    return func