from mywash_admin.lib.coupon import BaseCoupon
from api.models import UserOrderCoupon as UOCModel
import datetime
from datetime import datetime
from mywash_admin import app
# Coupon for MYWASHDG, Dude Geenie coupon

db = app.config['MONGO_CLIENT']['dealsup']


class Coupon(BaseCoupon):
    def __init__(self, coupon_id, service, user_id):
        super(Coupon, self).__init__(coupon_id, service, user_id)

    def _validate_coupon_usage_count_per_day(self):
        # This coupon can be used for a max count of 30
        date_today = datetime.strptime(str(datetime.today().date()), '%Y-%m-%d')
        order_count = 0
        try:
            order_count = db.orders.find({
                "coupon.name": self.coupon_data.data['name'],
                "created_date": {'$gte': date_today},
                "status": {'$nin': [5, 6, '5', '6', 'order_cancelled', 'order_rejected']}
                }).count()
        except Exception, e:
            return {'status': "failure", 'error': "db"}
        coupon_per_day_count = self.coupon_data.data['count_per_day']
        if order_count >= coupon_per_day_count:
            return {'status': "failure", 'error': "The coupon code entered by you has already been used to its maximum count for the day. Please try again tomorrow."}
        else:
            return {'status': "success"}

    # coupon not limited
    def _validate_one_coupon_per_day(self):
        return {'status': "success"}