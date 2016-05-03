import bson
from datetime import datetime
from mywash_admin import db
from sqlalchemy.dialects.postgresql import JSONB
import copy


class BaseModel(db.Model):
    """
    This model is used to subclass other models.
    """
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    str_id = db.Column(db.String(100), unique=True)
    data = db.Column(JSONB)
    creation_time = db.Column(db.DateTime, default=datetime.utcnow())
    last_modified = db.Column(db.DateTime, default=datetime.utcnow())

    def __init__(self, data=None):
        self.data = data
        self.str_id = str(bson.ObjectId())

    def __repr__(self):
        return u"<BaseModel %s>" % self.str_id

    def update_data_field(self, **kwargs):
        temp_data = copy.deepcopy(self.data) or {}
        temp_data.update(kwargs)
        self.data = temp_data
