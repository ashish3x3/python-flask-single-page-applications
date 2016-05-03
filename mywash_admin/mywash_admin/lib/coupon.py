from mywash_admin import app
import bson
from datetime import datetime
import inspect
from api.models import UserOrderCoupon as UOCModel
from api.models import Coupon as CouponModel
from bson.objectid import ObjectId
from sqlalchemy import update
from mywash_admin import db as pgdb

db = app.config['MONGO_CLIENT']['dealsup']


class BaseCoupon(object):
    """docstring for BaseCoupon"""
    def __init__(self, coupon_id, service_type, user_id=None):
        super(BaseCoupon, self).__init__()
        try:
            self.coupon_id = coupon_id
            self.user_id = user_id
            self.service_type = service_type
            self.coupon_data = CouponModel.query.filter(CouponModel.str_id == self.coupon_id).first()
            self.user_details = db.users.find_one({"_id": ObjectId(self.user_id)})
        except Exception, e:
            self.coupon_id = None
            self.user_id = None
            self.service_type = None
            self.coupon_data = None
            print e

        self.now = datetime.utcnow()

    def _validate_is_active(self):
        if not self.coupon_data.is_active:
            return {'status': "failure", 'error': "This coupon is invalid."}
        else:
            return {'status': "success"}

    def _validate_expiry_date(self):
        if self.now > self.coupon_data.expiry_date:
            return {'status': "failure", 'error': "The coupon code entered by you has expired. Please enter a valid code."}
        else:
            return {'status': "success"}

    def _validate_service_type(self):
        if self.service_type not in self.coupon_data.service.split(','):
            return {'status': "failure", 'error': "The coupon code entered by you is Invalid. Please enter a valid code."}
        else:
            return {'status': "success"}

    # method to validate the count of usage of coupon per user
    def _validate_coupon_count(self):
        # here coupon_id is str_id in coupon table
        coupon_usage_count = 0
        try:
            coupon_usage_count = UOCModel.query.filter(UOCModel.coupon == self.coupon_id).count()
        except Exception, e:
            return {'status': "failure", 'error': "db"}
        if coupon_usage_count >= int(self.coupon_data.data['count']):
            return {'status': "failure", 'error': "The coupon code entered by you has already been used. Please enter a valid code."}
        else:
            return {'status': "success"}

    # method to validate the count of usage of coupon per user
    def _validate_one_coupon_per_day(self):
        # here coupon_id is str_id in coupon table
        date_today = datetime.strptime(str(datetime.today().date()), '%Y-%m-%d')
        order_count = 0
        try:
            order_count = db.orders.find({
                "coupon.str_id": self.coupon_data.str_id,
                "user_id": self.user_details['user_id'],
                "created_date": {'$gte': date_today},
                "status": {'$nin': ['order_cancelled', 'order_rejected']}
            }).count()
        except Exception, e:
            return {'status': "failure", 'error': "db error"}
        if order_count >= 1:
            return {'status': "failure", 'error': "The coupon code entered by you has already been used for the day. Please try again tomorrow."}
        else:
            return {'status': "success"}


    def validate(self):
        data = UOCModel.query.filter(
            UOCModel.user == self.user_id,
            UOCModel.coupon == self.coupon_id,
            UOCModel.is_active == True
        )

        if data.count():
            for data_row in data:
                if not data_row.order:
                    data.is_active = False
            pgdb.session.commit()

        for member in inspect.getmembers(self):
            if member[0].startswith("_validate_"):
                result = getattr(self, member[0])()
                if result['status'] == "failure":
                    return result
        return {'status': "success"}