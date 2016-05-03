from mywash_admin.lib.coupon import BaseCoupon
from mywash_admin import db as pgdb
from mywash_admin import app

db = app.config['MONGO_CLIENT']['dealsup']
# Coupon for MYWASHHELP
# 5617679efa1d860cc3066c43


class Coupon(BaseCoupon):
    def __init__(self, coupon_id, service, user_id):
        super(Coupon, self).__init__(coupon_id, service, user_id)

    def _validate_count_per_user_overtime(self):
        # here coupon_id is str_id in coupon table
        order_count = 0
        try:
            order_count = db.orders.find({
                "coupon.str_id": self.coupon_data.str_id,
                "user_id": self.user_details['user_id'],
                "status": {'$nin': ['order_cancelled', 'order_rejected']}
            }).count()
        except Exception, e:
            return {'status': "failure", 'error': "db error"}
        if order_count >= 1:
            return {'status': "failure", 'error': "The coupon code entered by you has already been used."}
        else:
            return {'status': "success"}