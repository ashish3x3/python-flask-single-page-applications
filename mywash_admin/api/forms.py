from flask.ext.wtf import *
from datetime import datetime


class VendorsForm(Form):
    name = TextField()
    phone = TextField()
    email = TextField(100)
    address = TextField()
    joining_date = DateTimeField()
    services = IntegerField()
    is_active = BooleanField()
