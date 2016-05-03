from mywash_admin.lib.coupon import BaseCoupon
from api.models import UserOrderCoupon as UOCModel
import datetime
#from 55c053aefa1d862181762992 import Coupon
# Coupon for MYWASHEST


class Coupon(BaseCoupon):
    def __init__(self, coupon_id, service, user_id):
        super(Coupon, self).__init__(coupon_id, service, user_id)