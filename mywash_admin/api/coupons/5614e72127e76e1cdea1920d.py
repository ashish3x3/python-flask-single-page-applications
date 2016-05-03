from mywash_admin.lib.coupon import BaseCoupon
from api.models import UserOrderCoupon as UOCModel
import datetime
from datetime import datetime
from mywash_admin import app

db = app.config['MONGO_CLIENT']['dealsup']

# Coupon for MYWASHCR100
class Coupon(BaseCoupon):
    def __init__(self, coupon_id, service, user_id):
        super(Coupon, self).__init__(coupon_id, service, user_id)

