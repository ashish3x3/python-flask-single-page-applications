from boiler.models.database import logger as mongo_logger
from boiler.models.dao import ordersDAO
from boiler.models.dao import schedulesDAO
from boiler.models.dao import addressDAO
from boiler.models.dao import itemsDAO
from boiler.models.dao import usersDAO
from flask import jsonify, request, session
from flask import render_template, redirect, make_response
import Constants
import copy, json, logging, requests
from boiler.renderer import commonrender
import emails, sms
from boiler import app
from boiler import config
from datetime import datetime
from urllib2 import URLError
import traceback
import sys
import requests
import pprint
from requests_futures.sessions import FuturesSession

redis_client = config.REDIS_CLIENT
arequests = FuturesSession(max_workers=1)


def submit_order():
    result = copy.deepcopy(session.get("header", {}))
    if request.method == 'POST':
        if session.get("id", None) is None:
            return jsonify({'data': {'status': 'failure', 'error': 'user not logged in.'}}), 403
        try:
            # Order Validation Script:
            copy_data = copy.deepcopy(request.form)
            copy_data = copy_data.copy()
            if not copy_data.get("service"):
                result.update({"status": 204, "body": {"status": False, "message": "Please Select a Service type"}})
                return jsonify(result)

            if not copy_data.get("address_id"):
                result.update({"status": 204, "body": {"status": False, "message": "Please Select a address"}})
                return jsonify(result)

            address = addressDAO.get_address(copy_data.get("address_id"))
            if not address['result'][0]['assigned_hub']:
                result.update({"status": 403, "body": {"status": False, "message": "Locality not provided in address."}})
                return jsonify(result)
            if not copy_data.get("pickup_time"):
                result.update({"status": 204, "body": {"status": False, "message": "Please Select a pick up time"}})
                return jsonify(result)

            if not compare(copy_data.get("pickup_date_submit", ""), copy_data.get("schedule_date_submit","")):
                result.update({"status": 204, "body": {"status": False, "message": "Do you want to interchange pickup and delivery ?!!"}})
                return jsonify(result)

            user_data = usersDAO.get_user(session.get("id", None))
            if 'phone' in user_data and user_data['phone']:
                copy_data.add('phone', user_data['phone'])

            pickup_schedule = schedulesDAO.base_schedule()
            delivery_schedule = schedulesDAO.base_schedule()

            pickup_schedule["address_id"] = copy_data.get("address_id")
            delivery_schedule["address_id"] = copy_data.get("address_id")
            pickup_schedule["is_pickup"] = True
            delivery_schedule["is_pickup"] = False
            try:
                pickup_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data.get("pickup_time"))]
            except KeyError:
                result.update({"status": 500, "body": {"status": False, "message": "Timeslot doesn't exist."}})
            pickup_schedule["schedule_date"] = copy_data.get("pickup_date_submit")
            pickup_schedule["schedule_date_new"] = datetime.strptime(copy_data.get("pickup_date_submit"), "%Y/%m/%d")

            try:
                delivery_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data.get("schedule_time"))]
            except Exception, e:
                result.update({"status": 500, "body": {"status": False, "message": "Timeslot doesn't exist."}})
            if copy_data.getlist("schedule_date_submit")[0] != "":
                delivery_schedule["schedule_date"] = copy_data.getlist("schedule_date_submit")[0]
                delivery_schedule["schedule_date_new"] = datetime.strptime(copy_data.getlist("schedule_date_submit")[0], "%Y/%m/%d")
            else:
                copy_data.getlist("schedule_date_submit")[1]
            pickup_date = copy_data['pickup_date']
            pickup_time = int(copy_data['pickup_time'])
            pickup_timings = config.TIMESLOTS.get(str(pickup_time))

            schedule_date = copy_data['schedule_date']
            schedule_time = int(copy_data['schedule_time'])
            schedule_timings = config.TIMESLOTS.get(str(schedule_time))

            washtype = copy_data['washtypes']
            phone = copy_data['phone']
            address = addressDAO.get_address(copy_data.get("address_id"))
            locality = address['result'][0]['locality']['map_string']
            apartment_number = address['result'][0]['apartment_number']
            address_1 = address['result'][0]['address_1']
            city = address['result'][0]['city']
            service_type = copy_data['service']
            js_order_form_data = {'pickup_time': pickup_time,
                    'pickup_date': pickup_date,
                    'pickup_timings': pickup_timings,
                    'schedule_date': schedule_date,
                    'schedule_time': schedule_time,
                    'schedule_timings': schedule_timings,
                    'washtype': washtype.upper(),
                    'phone': phone,
                    'apartment_number': apartment_number,
                    'address_1': address_1,
                    'city': city,
                    'locality': locality,
                    'service_type': service_type.upper()}
            order_form_data = copy.deepcopy(copy_data)
            result.update({"status": 204, "body": {"status": True, "order_form_data": order_form_data}});
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log = {
                'event': 'order_session_store',
                'exception': repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                'user_id': session.get("id", None),
                'order_form_data': json.dumps(copy.deepcopy(request.form))
            }
            mongo_logger.exception_logs.insert(log)
        return jsonify(result)
    else:
        return jsonify({'status': 'failure', 'message': 'unauthorized access.'}), 403


def coupon_verify():
    result = copy.deepcopy(session.get("header", {}))
    if request.method == 'POST':
        if session.get("id", None) is None:
            return jsonify({'data': {'status': 'failure', 'error': 'user not logged in.'}}), 403
        try:
            copy_data = copy.deepcopy(request.form)

            pickup_schedule = schedulesDAO.base_schedule()
            delivery_schedule = schedulesDAO.base_schedule()

            pickup_schedule["address_id"] = copy_data["address_id"]
            delivery_schedule["address_id"] = copy_data["address_id"]

            pickup_schedule["is_pickup"] = True
            delivery_schedule["is_pickup"] = False
            try:
                pickup_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["pickup_time"])]
            except KeyError:
                result.update({"status": 500, "body": {"status": False, "message": "Timeslot doesn't exist."}})
            
            pickup_schedule["schedule_date"] = copy_data["pickup_date_submit"]
            pickup_schedule["schedule_date_new"] = copy_data["pickup_date_submit"]

            try:
                delivery_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["schedule_time"])]
            except Exception, e:
                result.update({"status": 500, "body": {"status": False, "message": "Timeslot doesn't exist."}})
            
            if copy_data["schedule_date_submit"] != "":
                delivery_schedule["schedule_date"] = copy_data["schedule_date_submit"]
                delivery_schedule["schedule_date_new"] = copy_data["schedule_date_submit"]
            else:
                copy_data["schedule_date_submit"]
            coupon_name = ''
            service_type = ''
            if 'service' in copy_data and copy_data['service']:
                service_type = copy_data['service']
            if 'coupon' in copy_data and copy_data['coupon']:
                coupon_name = copy_data.get("coupon").lower().strip()
            user_id = session.get('id', '')
            if coupon_name:
                if service_type:
                    try:
                        payload_data = {'user_id': user_id, 'coupon': coupon_name, 'service':service_type}
                        url = config.API_SERVER['private_dashboard'] + "/api/couponverify/coupon"
                        r = requests.post(url, data=payload_data)
                        coupon_data = r.json()
                       
                        ##Must get Terms and conditions here and show it on notification
                        if coupon_data['status'] == 'success':
                            result.update({"status": 204, "body": {"status": True, "terms": coupon_data['terms']}})
                        else:
                            result.update({"status": 204, "body": {"status": False, "message": coupon_data['error']}})
                           
                        return jsonify(result)
                    except URLError, e:
                        return result.update({"status": 403, "body": {"status": True, "message": "Some error occured. Contact customer support."}})
            else:
                return result.update({"status": 403, "body": {"status": True, "message": "Some error occured. Contact customer support."}})
        except Exception, e:
            return result.update({"status": 403, "body": {"status": True, "message": "Some error occured. Contact customer support."}})
    else:
        try:
            result.update(addressDAO.get_user_address(session.get("id")))
        except Exception, e:
            result = []
    return jsonify(result)


def complete_order():
    result = copy.deepcopy(session.get("header", {}))
    if request.method == 'POST':
        if session.get("id", None) is None:
            return jsonify({'data': {'status': 'failure', 'error': 'user not logged in.'}}), 403
        try:
            data = ordersDAO.base_order()
            copy_data = copy.deepcopy(request.form)

            pickup_schedule = schedulesDAO.base_schedule()
            delivery_schedule = schedulesDAO.base_schedule()

            pickup_schedule["address_id"] = copy_data["address_id"]
            delivery_schedule["address_id"] = copy_data["address_id"]

            pickup_schedule["is_pickup"] = True
            delivery_schedule["is_pickup"] = False
            try:
                pickup_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["pickup_time"])]
            except KeyError:
                result.update({"status": 500, "body": {"status": False, "message": "Timeslot doesn't exist."}})
            
            pickup_schedule["schedule_date"] = copy_data["pickup_date_submit"]
            pickup_schedule["schedule_date_new"] = datetime.strptime(pickup_schedule["schedule_date"], "%Y/%m/%d")

            try:
                delivery_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["schedule_time"])]
            except Exception, e:
                result.update({"status": 500, "body": {"status": False, "message": "Timeslot doesn't exist."}})
            
            if copy_data["schedule_date_submit"] != "":
                delivery_schedule["schedule_date"] = copy_data["schedule_date_submit"]
                delivery_schedule["schedule_date_new"] = datetime.strptime(delivery_schedule["schedule_date"], "%Y/%m/%d")

            coupon_name = ""
            service_type = copy_data['service']
            user_order_coupon_id = ""
            user_id = session.get('id', '')
            is_coupon_valid = False
            if 'coupon' in copy_data and copy_data['coupon']:
                coupon_name = copy_data.get("coupon").lower().strip()
            if coupon_name and service_type:
                try:
                    url = config.API_SERVER['private_dashboard'] + "/api/couponverify"
                    payload_data = {'user_id': user_id, 'coupon': coupon_name, 'service':service_type}
                    r = requests.post(url, data=payload_data)
                    result_data = r.json()

                    if result_data['status'] == 'success':
                        if 'uoc_id' in result_data and result_data['uoc_id']:
                            user_order_coupon_id = result_data['uoc_id']
                            is_coupon_valid = True
                    else:
                        if 'message' in result_data and result_data['message']:
                            result.update({"status": 204, "body": {"status": False, "message": result_data['message']}})
                            is_coupon_valid = False
                        else:
                            result.update({"status": 204, "body": {"status": False, "message": result_data['error']}})
                            is_coupon_valid = False
                    if not is_coupon_valid:
                        return jsonify(result)
                except URLError, e:
                    print e
                    result.update({"status": 204, "body": {"status": False, "message": "Failed while placing order using coupon"}})
                    return result

            pickup_schedule["is_completed"] = False
            delivery_schedule["is_completed"] = False

            pickup_schedule["is_active"] = True
            delivery_schedule["is_active"] = True

            data["service_type"] = service_type
            data["pickup_id"] = schedulesDAO.add_schedule(pickup_schedule)
            data["delivery_id"] = schedulesDAO.add_schedule(delivery_schedule)

            data["service_type"] = service_type
            data["special_instructions"] = copy_data['special_instructions'] if 'special_instructions' in copy_data else ' '
            data["address_id"] = copy_data["address_id"]

            data["user_id"] = session.get("id", None)
            
            temp_phone = copy_data.get('phone', None)
            if temp_phone is not None:
                data["phone"] = temp_phone
            else:
                user_data = usersDAO.get_user(session.get("id", None))
                data["phone"] = user_data.get('phone', None)

            data["type"] = copy_data["washtypes"].split(",")

            if is_coupon_valid and coupon_name:
                try:
                    url = config.API_SERVER['private_dashboard'] + "/api/coupon/name/"+coupon_name
                    r = requests.get(url)
                    coupon_data = r.json()
                    data["coupon"] = {
                        'name': coupon_name,
                        'str_id': coupon_data['str_id']
                    }
                    data['discount'] = {
                        'amount': coupon_data['amount'] if 'amount' in coupon_data else 0,
                        'min_order': coupon_data['min_order'] if 'min_order' in coupon_data else 0,
                        'max': int(coupon_data['max']) if 'max' in coupon_data else 0,
                        'percentage': coupon_data['percentage'] if 'percentage' in coupon_data else False
                    }
                except URLError, e:
                    print e
            data["order_id"] = 'EX' + data["order_id"] if data["service_type"] == "express" else data["order_id"]

            order_id = ordersDAO.submit_order(data)
            

            #below code to update order column in user order coupon table
            try:
                url = config.API_SERVER['private_dashboard'] + "/api/couponverify"
                payload = {'method': 'update', 'uoc_str_id': user_order_coupon_id, 'order': order_id}
                r = requests.put(url, data=payload)
            except URLError, e:
                print e

        except Exception, e:
            print e
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log = {
                'event': 'order_placement',
                'exception': repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                'user_id': session.get("id", None),
                'order_form_data': json.dumps(copy.deepcopy(request.form))
            }

            mongo_logger.exception_logs.insert(log)
            order_id = 0

        if order_id > 0:
            result.update({"status": 204, "body": {"status": True, "order": {"id":order_id}}})
            if 'email' in session["header"]["user"]:
                emails.email_order_placed.delay({"order_id": str(order_id), "email": session["header"]["user"]["email"],"name":session['header']['user']["name"],"service_type":data["service_type"]})
            sms.sms_order_placed.delay({"order_id": str(order_id), "name":session['header']['user']["name"]})
        else:
            result.update({"status": 204, "body": {"status": False, "message": "Failed to order"}})

        # Assign hub for the order asyncronously by using its address
        try:
            arequests.put(app.config['API_SERVER']['private_dashboard'] + "/api/address/" + data["address_id"], data={'refresh_hub': 'true'})
        except Exception, e:
            pass
        return jsonify(result)
    else:
        return jsonify({'status': 'failure', 'message': 'unauthorized access.'}), 403


def validate_phone(phone):
    import re
    if len(phone) > 13 or len(phone) < 10:
        return False
    p = re.compile('(^[+0-9]{1,3})*([0-9]{10,11}$)')
    if p.match(phone) != None:
        return True
    else:
        return False


def compare(pickup, delivery):
    return True
    if int(delivery[-4:]) >= int(pickup[-4:]):
        return True
    else:
        return False


@commonrender('order/review_order.jinja')
def review_order():
    result = copy.deepcopy(session.get("header", {}))
    copy_data = copy.deepcopy(order_form_data)
    if session.get('id', ''):
        if copy_data is not None:
            pickup_date = copy_data['pickup_date'] if 'pickup_date' in copy_data else None
            pickup_time = copy_data['pickup_time']
            pickup_timings = config.TIMESLOTS.get(str(pickup_time))

            schedule_date = copy_data['schedule_date']
            schedule_time = copy_data['schedule_time']
            schedule_timings = config.TIMESLOTS.get(str(schedule_time))

            washtype = copy_data['washtypes']
            phone = copy_data['phone']
            address = addressDAO.get_address(copy_data['address_id'])
            apartment_number = address['result'][0]['apartment_number']
            address_1 = address['result'][0]['address_1']
            city = address['result'][0]['city']
            service_type = copy_data['service']

            result.update({
                'data': {
                    'pickup_time': pickup_time,
                    'pickup_date': pickup_date,
                    'pickup_timings': pickup_timings,
                    'schedule_date': schedule_date,
                    'schedule_time': schedule_time,
                    'schedule_timings': schedule_timings,
                    'washtype': washtype,
                    'phone': phone,
                    'apartment_number': apartment_number,
                    'address_1': address_1,
                    'city': city,
                    'service_type': service_type
                }
            })
            return result
        else:
            log = {
                'event': 'review_order_missing_session',
                'user_id': session.get("id", None),
            }
            mongo_logger.exception_logs.insert(log)
            return redirect("/verifyphone")
    else:
        return redirect("/login")


@commonrender('order/order_history/history.jinja')
def get_top():
    access_token = session.get("access_token")
    if access_token is None:
        return redirect("/login")
    print "session id ", session.get("id","0")
    result = copy.deepcopy(session.get("header", {}))
    result.update(ordersDAO.get_top_orders(session.get("id", "0")))
    return result


def cancel_order():
    order_id = request.args.get("order_id", 0)
    result = copy.deepcopy(session.get("header", {}))
    result1 = ordersDAO.order_status_update(order_id, 'order_cancelled')

    if result1:
        result.update({"status": 204, "body": {"status": True, "order": {"id": order_id}}})
        try:
            url = config.API_SERVER['private_dashboard'] + "/api/couponverify"
            payload = {'method': 'delete', 'order': order_id}
            r = requests.put(url, data=payload)
        except URLError, e:
            print e
        emails.email_order_cancelled.delay({"order_id": str(order_id), "email": session["header"]["user"]["email"],"name":session['header']['user']["name"]})
        sms.sms_order_cancelled.delay({"order_id": str(order_id), "email": session["header"]["user"]["email"],"name":session['header']['user']["name"]})
    else:
        result.update({"status": 204, "body": {"status": False, "message": "Failed to  Cancel order"}})
    return jsonify(result)


def get_order(order_id):
    result = copy.deepcopy(session.get("header", {}))
    order = ordersDAO.get_order(order_id)
    if order.get("status", 1) == 5:
        return redirect("/getreceipt/" + str(order_id))
    else:
        return redirect("/getstatus/" + str(order_id))


@commonrender('order/status.jinja')
def get_status(order_id):
    result = copy.deepcopy(session.get("header", {}))
    data_form = dict(copy.deepcopy(request.args)) or {'transaction_status': '', 'transaction_message': ''}
    if session.get('id', ''):
        order = ordersDAO.get_order(order_id)
        status_text = order.get("status")
        try:
            if int(status_text) in range(1, 7):
                if status_text == 1:
                    status_text = 'order_placed'
                elif status_text == 2:
                    status_text = 'pickup_success'
                elif status_text == 3:
                    status_text = 'delivery_ready'
                elif status_text == 4:
                    status_text = 'clothes_delivered'
                elif status_text == 5:
                    status_text = 'order_cancelled'
                elif status_text == 6:
                    status_text = 'order_rejected'
        except Exception, e:
            pass
        status_detail = app.config['GET_STATUS_DETAIL'](status_text)
        if not status_detail['visible_to_customer']:
            status_detail = app.config['GET_STATUS_DETAIL'](status_detail['customer_status'])
        order.update({"status_text": status_detail['name']})
        order.update({"status": status_detail['name_id']})
        order.update({"status_group": status_detail['group_id']})
        order.update({"status_group_name": status_detail['group_name']})
        order.update({'order_id': order['order_id']})
        order.update({'created_date': order['created_date']})
        order.update(data_form)
        if isinstance(order['type'], list):
            temp = ""
            for i in order['type']:
                temp += " " + Constants.TYPE_DICT.get(i, "0") + ","
            order['type'] = temp.strip(",")
        else:
            order['type'] = Constants.TYPE_DICT.get(order['type'], "0")
        result.update(order)

        if 'coupon' in order and 'name' in order['coupon']:
            try:
                url = config.API_SERVER['private_dashboard'] \
                    + "/api/couponverify/order/" + order_id
                r = requests.get(url)
                coupon_data = r.json()

                if coupon_data['status'] == 'success':
                    result['coupon_applied'] = coupon_data
                else:
                    result['coupon_applied'] = coupon_data
            except URLError, e:
                print e
        else:
            result['coupon_applied'] = {'status': 'failure'}
        return result
    else:
        return redirect("/login")


def update_status(order_id, status):
    # use ordersDAO.update_order
    status = int(status)
    result = copy.deepcopy(session.get("header", {}))
    if not (status > 0 and status < 7):
        return result.update({"status": 204, "body": {"status": False,
            "message": "Requested status is invalid."}})
    if ordersDAO.update_order(order_id, {'status': status}):
        result.update({"status": 204, "body": {"status": True,
            "message": "Order updated success."}})
    else:
        result.update({"status": 204, "body": {"status": False,
            "message": "Order update fail."}})
    return jsonify(result)


@commonrender('order/order_history/receipt.jinja')
def get_receipt(order_id):
    result = copy.deepcopy(session.get("header", {}))
    result.update(ordersDAO.get_order(order_id))
    return result


def trending():
    count = request.args.get("count", 5)
    result = copy.deepcopy(session.get("header", {}))
    result.update(ordersDAO.get_trending(count))
    return result


def addrating():
    order_id = request.args.get("order_id", "")
    rating = request.args.get("rating", 5)
    result1 = ordersDAO.add_rating(order_id, rating)
    result = copy.deepcopy(session.get("header", {}))

    if result1:
        result.update({"status": 204, "body": {"status": True}})
    else:
        result.update({"status": 204, "body": {"status": False, "message": "Failed to add rating"}})
    return jsonify(result)


def additems():
    order_id = request.args.get("order_id", "")
    non_data = request.args.get("data", "")
    result = copy.deepcopy(session.get("header", {}))
    json_data = json.loads(non_data)
    data = json.loads(non_data)
    try:
        price = 0
        result_data = []
        for x in data:
            data = {}
            data["type"] = x.get("type")
            data["name"] = x.get("name")
            data["value"] = x.get("value")
            item = itemsDAO.get_item(x.get("name")).get("result")[0]
            data["title"] = item.get("title", "")
            if int(data.get("type")) == 0:
                price += int(data.get("value")) * item.get("price").get(
                    "laundry")
                data["price"] = int(data.get("value")) * item.get("price").get(
                    "laundry")
                data["text_type"] = "Wash & Iron"
            elif int(data.get("type")) == 1:
                price += int(data.get("value")) * item.get("price").get(
                    "dry_cleaning")
                data["price"] = int(data.get("value")) * item.get("price").get(
                    "laundry")
                data["text_type"] = "Dry Cleaning"
            result_data.append(data)

        try:
            ordersDAO.update_order(order_id, {"order_price": price,
             "final_price": price})
        except Exception as e:
            logging.error("Failed to update order price with excepiton "
                + str(e))
        result1 = ordersDAO.add_items(order_id, {"order_items": result_data})
    except Exception as e:
        logging.error("Data is not passed to add items with exception "
            + str(e))
        result1 = None
   
    if result1:
        order = ordersDAO.get_order(order_id)
        user = usersDAO.get_user(order.get("user_id"))
        #emails.email_order_invoice.delay({"order_id":str(order_id),"email":user.get("email"),"name":user.get("name")})
        #sms.sms_order_invoice.delay({"order_id":str(order_id),"email":user.get("email"),"name":user.get("name")})
        result.update({"status": 204, "body": {"status": True}})
    else:
        result.update({"status": 204, "body": {"status": False, "message": "Failed to add Items to Order"}})
    return jsonify(result)


#@commonrender('order/schedule.jinja')
def order_schedule():
    access_token = session.get("access_token")
    if access_token is None:
        return redirect("/login")

    result = copy.deepcopy(session.get("header", {}))

    if session.get('id', ''):
        user_data = usersDAO.get_user(session.get('id', ''))
        if 'name' in user_data and user_data['name']:
            result['user']['name'] = user_data['name']
        if 'phone' in user_data and user_data['phone']:
            result['user']['phone'] = user_data['phone']
        if 'email' in user_data and user_data['email']:
            result['user']['email'] = user_data['email']
        if not ('phone_is_valid' in user_data) or not user_data['phone_is_valid']:
            return redirect("/verifyphone")

    result.update(itemsDAO.get_all_items())
    result.update({
        "address_list": dict(enumerate(addressDAO.get_user_address(session.get("id","")).get("result"))),
        'user_id': session.get('id', None)
    })
    resp = make_response(render_template('order/schedule.jinja', **result))
    user_token_mywash = request.cookies.get('_utmw')

    #checking if _utmw cookie not exists
    sess_id = session.get("id")
    if sess_id:
        # if cookie not exists checks if user logged in and then sets cookie
        if not user_token_mywash:
            dat = usersDAO.base_user(sess_id)
            user_token_mywash = dat['_id']
            resp.set_cookie('_utmw', user_token_mywash)
        else:
            #having token and session login
            #if user is logged in check if objectid matches utm cookie else change utm
            newUser = usersDAO.base_user(sess_id)
            newUser_utmw = newUser['_id']
            #if the tokens are not equals change utm cookie
            if user_token_mywash != newUser_utmw:
                resp.set_cookie('_utmw', newUser_utmw)#setting correct users token

    return resp


@commonrender('website/estimate.jinja')
def estimator():
    result = copy.deepcopy(session.get("header", {}))
    result.update(itemsDAO.get_all_items())
    result.update({"address_list": dict(enumerate(addressDAO.get_user_address(session.get("id","")).get("result")))})
    return result


"""
On redirection from payment page Paytm sends the following parameters to /payment/success
>> ORDERID
>> STATUS  can be TXN_SUCCESS/TXN_FAILURE/TXN_PENDING
>> GATEWAYNAME can be ICICI/CITI/WALLET
>> RESPCODE
>> TXNDATE '2015-08-20 17:14:48.0'
>> TXNID
>> BANKTXNID
>> BANKNAME
>> PAYMENTMODE
>> MID
>> CURRENCY
>> RESPMSG
>> TXNAMOUNT
>> CHECKSUMHASH
"""


def payment():
    payment_res = None
    try:
        payment_res = copy.deepcopy(request.form)
        print ".................", payment_res
        result = requests.put(config.API_SERVER['private_dashboard'] + "/api/paytm/payment", data=payment_res).json()
        print ".................", result
        if result['status'] == 'success':
            if payment_res['RESPCODE'] == '01':
                return redirect(config.WEBSITE + '/getstatus/' + result['order_id'])
            else:
                log = {
                    'event': 'payment_failure',
                    'paytm_response': payment_res
                }
                mongo_logger.exception_logs.insert(log)
                return redirect(config.WEBSITE + '/getstatus/' + result['order_id'] + "?transaction_status=failure&transaction_message=" + payment_res['RESPMSG'])
        else:
            log = {
                'event': 'payment_failure',
                'response': result,
                'paytm_response': payment_res
            }
            mongo_logger.exception_logs.insert(log)
            return redirect(config.WEBSITE + '/orders')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log = {
            'event': 'payment_failure',
            'exception': repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            'form_data': json.dumps(copy.deepcopy(request.form)),
            'paytm_response': payment_res
        }
        mongo_logger.exception_logs.insert(log)
        return jsonify({'status': 'failure', 'error': str(e)}), 403
