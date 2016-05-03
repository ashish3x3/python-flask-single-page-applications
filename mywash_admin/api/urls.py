from mywash_admin import api
from controllers import *
from controllers import partner


api.add_resource(
    payment.PaytmPayment,
    "/api/paytm/payment",
    "/api/paytm/payment/<string:order_id>",
)

api.add_resource(
    payment.PaytmRefund,
    "/api/paytm/refund",
    "/api/paytm/refund/<string:order_id>",
)

api.add_resource(
    timeslot.TimeSlot,
    "/api/timeslot",
    "/api/timeslot/<string:str_id>"
)

api.add_resource(
    failure_reason.FailureReason,
    "/api/failurereason",
    '/api/failurereason/<regex("pickup|delivery|partial_payment"):reason_type>',
    "/api/failurereason/<string:reason_id>"
)

api.add_resource(
    items.OrderItems,
    '/api/orderitem',
    '/api/orderitem/<string:order_id>'
)

api.add_resource(
    invoice.Invoice,
    '/api/invoice/<string:order_id>'
)

api.add_resource(
    invoice.InvoiceSendToCustomer,
    '/api/invoice/send'
)

api.add_resource(
    invoice.InvoiceIntoDrive,
    '/api/saveinvoice/<string:order_id>'
)


api.add_resource(
    status.StatusList,
    '/api/statuslist'
)

api.add_resource(
    cancelled.Cancelled,
    '/api/cancelled',
    '/api/cancelled/<int:skip>/<int:limit>'
)

api.add_resource(
    completed.Completed,
    '/api/completed/<regex("\d{4}-\d{2}-\d{2}"):date>',
)

api.add_resource(
    items.Items,
    '/api/items',
    '/api/items/<string:item_id>'
)

api.add_resource(
    order.Order,
    '/api/order',
    '/api/order/<string:order_type>/<regex("\d{4}-\d{2}-\d{2}"):date>',
    '/api/order/<string:order_id>',
    '/api/order/<int:skip>/<int:limit>'
)

api.add_resource(
    order.OrderSearch,
    '/api/order/search/<string:term>/<int:skip>/<int:limit>',
    '/api/order/search/<string:status>/<string:term>/<int:skip>/<int:limit>'
)

api.add_resource(
    order.OrderAgent,
    '/api/order/agent/<regex("\d{4}-\d{2}-\d{2}"):date>/<string:agent_id>',
    "/api/order/agent/<string:type>/<string:agent_id>",
    '/api/order/agent/<string:type>/<regex("\d{4}-\d{2}-\d{2}"):date>/<string:agent_id>'
)


api.add_resource(
    pickup.PickupDate,
    "/api/pickup",
    "/api/pickup/<string:date>",
    "/api/pickup/<string:date>/<string:time>"
)

api.add_resource(
    delivery.DeliveryDate,
    "/api/delivery",
    "/api/delivery/<string:date>",
    "/api/delivery/<string:date>/<string:time>"
)

api.add_resource(
    delivery_progress.DeliveryProgress,
    "/api/ofd",
)

api.add_resource(
    delivery_progress.DeliveryProgressPopulate,
    "/api/ofd/search/<string:oid>"
)


api.add_resource(
    tagging.TaggingDate,
    "/api/tagging/",
    "/api/tagging/<string:tagging_type>",
    "/api/tagging/<string:tagging_type>/<string:date>",
    "/api/tagging/<string:tagging_type>/<string:date>/<string:time>"
)

api.add_resource(
    package.Packaging,
    "/api/package",
    "/api/package/<int:skip>/<int:limit>"
)


api.add_resource(
    tagging.Tags,
    '/api/tags/<string:order_ids>'
)

api.add_resource(
    tagging.TagBags,
    '/api/tagbags/<string:pickup_date>/<string:bag_name>'
)

api.add_resource(
    bundles.Bundle,
    '/api/bundle',
    '/api/bundle/<string:bundle_id>',
    '/api/bundle/<int:bundle_id>'
)

api.add_resource(
    bundles.Bundles,
    '/api/bundles',
    '/api/bundles/<string:datestamp>'
)


api.add_resource(
    misc.PickupSheetInfo,
    '/api/pickupsheetinfo/<string:order_ids>'
)

api.add_resource(
    misc.ServiceType,
    '/api/servicetype'
)


api.add_resource(
    users.User,
    '/api/user',
    '/api/user/<int:skip>/<int:limit>',
    '/api/user/<string:user_id>'

)

api.add_resource(
    vendors.Vendors,
    '/api/vendor',
    '/api/vendor/<string:arg>',
    '/api/vendor/<int:arg>/<int:limit>'
)

api.add_resource(
    vendors.VendorSearch,
    '/api/vendor/search',
    '/api/vendor/search/<string:term>',
    '/api/vendor/search/<string:term>/<int:skip>/<int:limit>'
)

api.add_resource(
    users.UserSearch,
    '/api/user/search/<string:term>/<int:skip>/<int:limit>'
)

api.add_resource(
    users.UserPhoneVerification,
    '/api/user/verifyphone'
)

api.add_resource(
    employees.Employee,
    '/api/employee',
    '/api/employee/<int:status>',
    '/api/employee/<string:emp_id>',
    '/api/employee/<int:skip>/<int:limit>',
    '/api/employee/<int:skip>/<int:limit>/<int:status>'
)

api.add_resource(
    employees.EmployeeLogin,
    '/api/employee/login'
)

api.add_resource(
    employees.EmployeeSearch,
    '/api/employee/search/<string:term>'

)

api.add_resource(
    employees.EmployeeVerification,
    '/api/employee/verify/<string:emp_phone>',
    '/api/employee/verify'
)

api.add_resource(
    address.Address,
    '/api/address',
    '/api/address/<string:address_id>'
)

api.add_resource(
    address.UserAddress,
    '/api/address/user/<string:user_id>'
)

api.add_resource(
    order.OrderHistory,
    '/api/orderhistory/<string:user_id>'
)

api.add_resource(
    hub.Hub,
    '/api/hub',
    '/api/hub/<int:hub_id>'
)

api.add_resource(
    coupon.CouponVerification,
    '/api/couponverify',
    '/api/couponverify/order/<string:order_id>',
    '/api/couponverify/verify/<string:uoc_id>',
    '/api/couponverify/<string:coupon>'
)

api.add_resource(
    coupon.Coupon,
    '/api/coupon',
    '/api/coupon/<string:coup_id>',
    '/api/coupon/<int:skip>/<int:limit>',
    '/api/coupon/<int:skip>/<int:limit>/<int:status>',
    '/api/coupon/name/<string:name>'
)


# Enterprise

api.add_resource(
    partner.Partner,
    '/api/partner',
)

api.add_resource(
    partner.PartnerUser,
    '/api/partner/<string:partner_id>/user',
    '/api/partner/<string:partner_id>/user/<string:user_id>',
)
api.add_resource(
    partner.PartnerUserSearch,
    '/api/partner/search/<string:partner_id>'
)

api.add_resource(
    partner.PartnerOrderHistory,
    '/api/partner/<string:partner_id>/orders',
    '/api/partner/<string:partner_id>/order/<string:order_id>',
)

##################################### MISC FOR ANDROID TESTING ################################

api.add_resource(
    misc.UserLogin,
    '/api/userlogin'
)

api.add_resource(
    misc.AndroidScopes,
    '/api/scopes'
)

api.add_resource(
    misc.AndroidConfig,
    '/api/androidconfig',
    '/api/androidconfig/<string:agent>'
)

api.add_resource(
    misc.SendSMS,
    '/api/sms'
)

api.add_resource(
    misc.PhoneVerification,
    '/api/userPhoneAuthentication'
)

api.add_resource(
    misc.PhonePushNotification,
    '/api/phonepushnotification'
)
