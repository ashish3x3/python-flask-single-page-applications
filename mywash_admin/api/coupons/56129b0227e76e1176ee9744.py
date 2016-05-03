from mywash_admin.lib.coupon import BaseCoupon

# Coupon for MYWASH50
class Coupon(BaseCoupon):
    def __init__(self, coupon_id, service, user_id):
        super(Coupon, self).__init__(coupon_id, service, user_id)


