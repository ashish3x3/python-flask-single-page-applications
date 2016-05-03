from boiler import app
import Constants
from datetime import datetime

#FB details settings for login authorization
@app.template_filter('is_admin')
def is_admin(value):
    if value.get('id') in Constants.ADMIN_IDS_FB:
        return True
    return False


@app.template_filter('slice_string')
def slice_string(value, start, end=None):
    if not isinstance(value, unicode):
        return ""

    if end is None:
        end = start
        start = 0
    
    return value[start:end] + "..."


@app.template_filter('date_lt')
def date_lt(date1, date2):
    patterns = [
        "%b %d %Y %H:%M",
        "%a, %d %b %Y %H:%M:%S %Z"
    ]
    d1 = None
    for pattern in patterns:
        try:
            d1 = datetime.strptime(date1, pattern)
        except Exception, e:
            pass
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    return d1 < d2


@app.template_filter('date_gt')
def date_gt(date1, date2):
    patterns = [
        "%b %d %Y %H:%M",
        "%a, %d %b %Y %H:%M:%S %Z"
    ]
    d1 = None
    for pattern in patterns:
        try:
            d1 = datetime.strptime(date1, pattern)
        except Exception, e:
            pass
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    return d1 > d2
