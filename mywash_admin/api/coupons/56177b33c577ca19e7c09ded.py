from mywash_admin.lib.coupon import BaseCoupon
from mywash_admin import db as pgdb
from mywash_admin import app
db = app.config['MONGO_CLIENT']['dealsup']


# Coupon for MWLO30
class Coupon(BaseCoupon):
    def __init__(self, coupon_id, service, user_id):
        super(Coupon, self).__init__(coupon_id, service, user_id)

    # method to validate the if the user is created by partner
    # def _validate_coupon_partner(self):
    #     coupon_conditions = self.coupon_data.data
    #     try:
    #         user = db.users.find_one({"user_id": self.user_details['user_id']})
    #     except Exception, e:
    #             return {'status': "failure", 'error': "db error"}
    #     if 'partner' in user:
    #         partner_id = user.get('partner', {}).get('id', '')
    #         if not partner_id.strip() == coupon_conditions['coupon_partner'].strip():
    #             return {'status': "failure", 'error': "The coupon code entered by you is invalid. Please enter a valid code."} 
    #         return {'status': "success"}
    #     else:
    #         return {'status': "failure", 'error': "The coupon code entered by you is invalid. Please enter a valid code."} 
