import bson
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy.dialects.postgresql import JSONB

from mywash_admin.lib.database.model import BaseModel
from mywash_admin import app, db

mongo_db = app.config['MONGO_CLIENT']['dealsup']


class OnlineTransaction(BaseModel):
    __tablename__ = 'online_transaction'

    txn_date = db.Column(db.DateTime, default=datetime.utcnow())
    is_active = db.Column(db.Boolean, default=False)
    txn_type = db.Column(db.String(10), default="payment")

    def __repr__(self):
        return '<transaction %s>' % self.id


class Reason(BaseModel):
    __tablename__ = 'reason'

    def __repr__(self):
        return '<Reason %s>' % self.id


class TimeslotBlock(BaseModel):
    __tablename__ = 'blocked_timeslots'

    blocked_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return '<TimeslotBlock %s>' % self.blocked_date


class OperationalCountry(BaseModel):
    __tablename__ = 'operational_country'
    # data: name, short

    city = db.relationship('OperationalCity', backref='country')

    def __repr__(self):
        return "<OperationalCountry %s>" % self.data['name']


class OperationalCity(BaseModel):
    __tablename__ = 'operational_city'
    # data: name, bounds

    country_id = db.Column(db.Integer, db.ForeignKey('operational_country.id'))
    mywashhub = db.relationship('MywashHub', backref='city')

    def __repr__(self):
        return "<OperationalCity %s>" % self.data['name']


class MywashHub(BaseModel):
    __tablename__ = 'mywashhub'
    # Use data field
    # name, short, address, phone
    vendor = db.relationship('Vendor', backref='mywashhub')
    employee = db.relationship('Employee', backref='mywashhub')
    city_id = db.Column(db.Integer, db.ForeignKey('operational_city.id'))

    def __repr__(self):
        return "<MywashHub %s>" % self.data['name']


VendorServices = db.Table(
    'vendor_servicetype_through',
    BaseModel.metadata,
    db.Column('vendor_id', db.Integer, db.ForeignKey('vendor.id')),
    db.Column('servicetype_id', db.Integer, db.ForeignKey('servicetype.id')),
    extend_existing=True
)


class ServiceType(BaseModel):
    __tablename__ = 'servicetype'

    name = db.Column(db.String(30))

    def __repr__(self):
        return "<ServiceType %s>" % self.name


class Vendor(BaseModel):
    __tablename__ = 'vendor'
    # Use data field
    # name, phone, email, address
    joining_date = db.Column(db.DateTime, default=datetime.utcnow())

    services = db.relationship(
        'ServiceType',
        secondary=VendorServices,
        backref=db.backref('vendors', lazy='dynamic'),
    )

    is_active = db.Column(db.Boolean, default=False)
    mywash_hub_id = db.Column(db.Integer, db.ForeignKey('mywashhub.id'))

    vendorhub = db.relationship('VendorHub', backref='vendor')
    tagbundle = db.relationship('TagBundle', backref='vendor')

    def __init__(self, data, joining_date=None, services=None, mywash_hub=None):
        super(Vendor, self).__init__(data)
        if joining_date is not None:
            self.joining_date = joining_date
        if services is not None:
            self.services = services
        if mywash_hub is not None:
            self.mywash_hub_id = mywash_hub

    def __repr__(self):
        return "<Vendor %s>" % self.data['name']


class VendorHub(BaseModel):
    __tablename__ = 'vendorhub'
    # Use data field
    # name, address, phone
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)


class Coupon(BaseModel):
    __tablename__ = 'coupon'

    start_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)

    # if there is a coupon referring to other coupon we refer it here
    alias_coupon = db.Column(db.String(100), default=None)
    created_by = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100),nullable=False)
    # here the user collection is in boiler mongo
    # user_order_coupon = db.relationship('userordercoupon',
    # secondary=user_order_coupon,backref=db.backref('coupons', lazy='dynamic'))

    def __repr__(self):
        return "<Coupon %s>" % self.data['name']


class UserOrderCoupon(BaseModel):
    # many to many relationship to
    # reference https://pythonhosted.org/Flask-SQLAlchemy/models.html
    __tablename__ = 'user_order_coupon'

    # db.ForeignKey('user.id'))
    user = db.Column(db.String(100))

    # db.ForeignKey('order.id')),
    order = db.Column(db.String(100))
    coupon = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return "<UserOrderCoupon %s>" % self.str_id

    def get_order(self):
        return mongo_db.orders.find_one({'_id': bson.ObjectId(self.order)})

    def get_user(self):
        return mongo_db.users.find_one({'_id': self.user})


class Partner(BaseModel):
    __tablename__ = 'partner'

    is_active = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    tag = db.Column(db.String(5), nullable=False, unique=True)
    salt = db.Column(db.String(100), nullable=False)
    is_sms_block = db.Column(db.Boolean, nullable=False, default=False)
    # here the user collection is in boiler mongo
    # user_order_coupon = db.relationship('userordercoupon',
    # secondary=user_order_coupon,backref=db.backref('coupons', lazy='dynamic'))

    def __repr__(self):
        return "<Partner %s>" % self.data['name']

    def __init__(self, data={}, salt=None):
        super(Partner, self).__init__(data)
        if salt is not None:
            self.salt = generate_password_hash(salt)


class Department(BaseModel):
    __tablename__ = 'department'

    employee = db.relationship('Employee', backref="department")

    def __repr__(self):
        return "<Department %s>" % self.data['name']


class Employee(BaseModel):
    __tablename__ = 'employee'

    # Use data field
    # name, phone, employee_id, shift
    is_active = db.Column(db.Boolean)
    hub_id = db.Column(db.Integer, db.ForeignKey('mywashhub.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    notification = db.Column(JSONB)
    login_creds = db.Column(JSONB)

    def __init__(self, data, hub_id=None, department_id=None):
        super(Employee, self).__init__(data)
        if hub_id is not None:
            self.hub_id = hub_id

        if department_id is not None:
            self.department_id = department_id

    def __repr__(self):
        return "<Employee %s>" % self.data['name']


class TagBundle(BaseModel):
    __tablename__ = 'tagbundle'

    name = db.Column(db.String(200))
    date = db.Column(db.DateTime)
    bags = db.Column(JSONB)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)

    def __init__(self, name, bags, date=None, data=None):
        super(TagBundle, self).__init__(data)
        self.name = name
        self.data = date
        if bags is not None:
            self.bags = bags
        if data is not None:
            self.data = data

    def __repr__(self):
        return "<TagBundle %s>" % self.name
