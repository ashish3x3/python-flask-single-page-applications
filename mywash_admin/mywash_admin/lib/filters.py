from mywash_admin import app


@app.template_filter('slice_string')
def slice_string(value, start, end=None):
    if not isinstance(value, unicode):
        return ""
    if end is None:
        end = start
        start = 0
    return value[start:end] + "..."


@app.template_filter('contains')
def contains(value, item):
    if not isinstance(value, list):
        return False
    return item in value
