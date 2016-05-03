from boiler import app
import static
import orders
import analytics
import login
import users
import address
import items
import coupons
import emails
import sms
import partner

if app.config['MAINTENANCE']:
    app.add_url_rule('/', view_func=login.maintainence_landing)
    app.add_url_rule('/<path:somepath>', view_func=login.maintainence_landing)
else:
    app.add_url_rule('/privacy', view_func=coupons.privacy, methods=['GET', 'POST'])
    app.add_url_rule('/orders', view_func=orders.get_top, methods=['GET', 'POST'])
    app.add_url_rule('/getorder/<order_id>', view_func=orders.get_order, methods=['GET', 'POST'])
    app.add_url_rule('/getstatus/<order_id>', view_func=orders.get_status, methods=['GET', 'POST'])
    app.add_url_rule('/updatestatus/<order_id>/<int:status>', view_func=orders.update_status, methods=['GET', 'POST'])
    app.add_url_rule('/getreceipt/<order_id>', view_func=orders.get_receipt, methods=['GET', 'POST'])

    app.add_url_rule('/items', view_func=items.get_all, methods=['GET', 'POST'])
    app.add_url_rule('/getitem/<item_id>', view_func=items.get_item, methods=['GET', 'POST'])
    app.add_url_rule('/getaddresslist', view_func=address.get_address, methods=['GET', 'POST'])
    app.add_url_rule('/submitorder', view_func=orders.submit_order, methods=['GET', 'POST'])
    app.add_url_rule('/cancelorder', view_func=orders.cancel_order, methods=['GET', 'POST'])
    app.add_url_rule('/submitaddress', view_func=address.submit_address, methods=['GET', 'POST'])
    app.add_url_rule('/submitaddresscors', view_func=address.submit_address_cors, methods=['POST'])
    app.add_url_rule('/updatelocality', view_func=address.update_locality, methods=['POST'])
    app.add_url_rule('/coupons', view_func=coupons.coupon_form, methods=['GET', 'POST'])
    app.add_url_rule('/referfriend', view_func=coupons.refer_form, methods=['GET', 'POST'])
    app.add_url_rule('/ratings', view_func=coupons.ratings, methods=['GET', 'POST'])
    app.add_url_rule('/help', view_func=coupons.help, methods=['GET', 'POST'])
    app.add_url_rule('/faq', view_func=coupons.faq, methods=['GET', 'POST'])
    app.add_url_rule('/applycoupon', view_func=coupons.apply_coupon, methods=['GET', 'POST'])
    app.add_url_rule('/validatecoupon/<string:order_id>', view_func=coupons.validate_coupon, methods=['GET', 'POST'])
    app.add_url_rule('/addrating', view_func=orders.addrating, methods=['GET', 'POST'])
    app.add_url_rule('/additems', view_func=orders.additems, methods=['GET', 'POST'])
    app.add_url_rule('/order_schedule', view_func=orders.order_schedule, methods=['GET', 'POST'])

    app.add_url_rule('/completeorder', view_func=orders.complete_order, methods=['GET', 'POST'])
    app.add_url_rule('/couponverify', view_func=orders.coupon_verify, methods=['GET', 'POST'])

    app.add_url_rule('/refer', view_func=orders.trending, methods=['GET', 'POST'])

    app.add_url_rule('/landing', view_func=login.landing, methods=['GET', 'POST'])
    app.add_url_rule('/estimate', view_func=orders.estimator, methods=['GET', 'POST'])

    app.add_url_rule('/', view_func=login.landing, methods=['GET', 'POST'])
    app.add_url_rule('/about', view_func=login.about, methods=['GET', 'POST'])
    app.add_url_rule('/terms', view_func=coupons.terms, methods=['GET', 'POST'])
    app.add_url_rule('/emailsubscribe', view_func=users.subscribe_email, methods=['GET', 'POST'])


    #sampel http://dealsup.in/emailsubscribe?email=raghub@gmail.com

    #sample for all the below routes pass access_token parameter
    app.add_url_rule('/googlelogin', view_func=login.google_login, methods=['GET', 'POST'])
    app.add_url_rule('/fblogin', view_func=login.fb_login, methods=['GET', 'POST'])
    app.add_url_rule('/twitterlogin', view_func=login.twitter_login, methods=['GET', 'POST'])
    app.add_url_rule('/verifyphone', view_func=login.verify_phone, methods=['GET', 'POST'])
    app.add_url_rule('/validate_phone_otp', view_func=login.validate_phone_otp, methods=['GET', 'POST'])
    app.add_url_rule('/edit_phone', view_func=login.edit_phone, methods=['GET', 'POST'])

    # MyWash

    app.add_url_rule('/order_history', view_func=static.order_history, methods=['GET', 'POST'])
    app.add_url_rule('/order_reciept', view_func=static.order_reciept, methods=['GET', 'POST'])
    app.add_url_rule('/order_status', view_func=static.order_status, methods=['GET', 'POST'])

    app.add_url_rule('/profile', view_func=static.basicinfo, methods=['GET', 'POST'])
    app.add_url_rule('/login', view_func=static.login, methods=['GET', 'POST'])

    app.add_url_rule('/price', view_func=items.get_all, methods=['GET', 'POST'])
    app.add_url_rule('/logout', view_func=login.logout, methods=['GET', 'POST'])
    app.add_url_rule('/celery', view_func=static.celery_test,methods=['GET','POST'])

    app.add_url_rule('/currentlocaldatetime', view_func=static.get_current_time, methods=['GET'])

    # User personal information editing url
    app.add_url_rule('/myprofile', view_func=users.user_profile, methods=['GET', 'POST'])
    app.add_url_rule('/editprofile', view_func=users.edit_profile, methods=['GET', 'POST'])
    app.add_url_rule('/address', view_func=address.show_address_edit_page, methods=['GET'])
    app.add_url_rule('/address/<string:address_id>', view_func=address.show_address_edit_page, methods=['GET'])

    # unsubscribe
    app.add_url_rule('/unsubscribe/<string:email>', view_func=emails.unsubscribe, methods=['GET', 'POST'])

    app.add_url_rule('/payments/success', view_func=orders.payment, methods=['GET', 'POST'])
    app.add_url_rule('/timeslots', view_func=static.timeslots, methods=['GET'])
    app.add_url_rule('/dashboard/address', view_func=static.dashboard_address, methods=['POST'])
    app.add_url_rule('/dashboard/address/<string:address_id>', view_func=static.dashboard_address, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/orderitem/<string:order_id>', view_func=static.order_item, methods=['GET'])
    app.add_url_rule('/paytm/payment/<string:order_id>', view_func=static.paytm_payment, methods=['GET'])
    app.add_url_rule('/13C8119BCAB31B5ADED9C94FAC94DE58.txt', view_func=login.verify_domain_auth, methods=['GET', 'POST'])

    # partner
    app.add_url_rule('/partner', view_func=partner.partner_login, methods=['GET', 'POST'])
    app.add_url_rule('/partner/register', view_func=partner.partner_register, methods=['GET', 'POST'])
    app.add_url_rule('/partner/logout', view_func=partner.partner_logout, methods=['GET', 'POST'])
    app.add_url_rule('/partner/validate_partner', view_func=partner.validate_partner_login, methods=['GET', 'POST'])
    app.add_url_rule('/partner/customer', view_func=partner.partner_customers, methods=['GET', 'POST'])
    app.add_url_rule('/partner/customer/<string:user_id>', view_func=partner.partner_customer_data, methods=['GET', 'POST'])
    app.add_url_rule('/partner/add/customer', view_func=partner.partner_add_customer, methods=['GET', 'POST'])
    app.add_url_rule('/partner/customer/search/<string:search>', view_func=partner.partner_search_customer, methods=['GET', 'POST'])
    app.add_url_rule('/partner/customer/order/<string:customer_id>', view_func=partner.partner_place_order, methods=['GET', 'POST'])
    app.add_url_rule('/partner/customer/profile/<string:customer_id>', view_func=partner.partner_customer_profile, methods=['GET', 'POST'])
    app.add_url_rule('/partner/customer/ordersubmit', view_func=partner.partner_submit_order, methods=['GET', 'POST'])
    app.add_url_rule('/partner/couponverify', view_func=partner.partner_coupon_verify, methods=['GET', 'POST'])
    app.add_url_rule('/partner/completeorder', view_func=partner.partner_complete_order, methods=['GET', 'POST'])
    app.add_url_rule('/partner/getorder/<string:customer_id>/<order_id>', view_func=partner.partner_get_order, methods=['GET', 'POST'])
    app.add_url_rule('/partner/orders', view_func=partner.partner_get_top, methods=['GET', 'POST'])
    app.add_url_rule('/partner/getstatus/<string:customer_id>/<order_id>', view_func=partner.partner_get_status, methods=['GET', 'POST'])
    app.add_url_rule('/partner/getreceipt/<string:customer_id>/<order_id>', view_func=partner.partner_get_receipt, methods=['GET', 'POST'])
    app.add_url_rule('/partner/cancelorder/<string:customer_id>', view_func=partner.partner_cancel_order, methods=['GET', 'POST'])
    app.add_url_rule('/partner/help', view_func=partner.partner_help, methods=['GET', 'POST'])
