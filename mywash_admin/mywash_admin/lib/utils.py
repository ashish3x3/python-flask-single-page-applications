import pytz
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader
import re

env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.dirname(__file__))))


def get_current_time(tz="Asia/Calcutta"):
    kol = pytz.timezone(tz)
    a = datetime.utcnow()
    a = a.replace(tzinfo=kol)
    return kol.fromutc(a).strftime("%Y-%m-%d %H:%M:%S")


def validateEmail(email):
    patt = r'^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$'
    return re.match(patt, email) is not None