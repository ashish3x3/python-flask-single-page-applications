from flask import request
from functools import wraps
from mywash_admin import app


def whitelist_filter_decorator(func):
    def decorator(*args, **kwargs):
        if request.host_url not in app.config['SITE_ACCESS_WHITELIST']:
            return {'status': 'failure', 'error': 'unauthorised request.'}, 403
        return func(*args, **kwargs)
    return decorator


def whitelist_filter(methods=[], perm=None):
    def class_rebuilder(cls):
        class NewClass(cls):
            def __getattribute__(self, *args):
                parent = super(NewClass, self)
                for method in methods:
                    if hasattr(parent, method):
                        return whitelist_filter_decorator(getattr(parent, method))
        return NewClass
    return class_rebuilder