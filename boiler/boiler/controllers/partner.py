import copy
import json
import requests
import emails
import sms
from boiler.models.database import logger as mongo_logger
from flask import jsonify, request, session
from flask import redirect
from boiler.renderer import commonrender
from boiler import app, config
from boiler.models.dao import usersDAO
from boiler.models.dao import addressDAO
from boiler.models.dao import itemsDAO
from datetime import datetime
import traceback
import sys
from boiler.models.dao import schedulesDAO
from boiler.models.dao import ordersDAO
import Constants
from requests_futures.sessions import FuturesSession
import re

from boiler.models.database import logger as mongo_logger
arequests = FuturesSession(max_workers=1)


@commonrender('partner/partner_login.jinja')
def partner_login():
    result = copy.deepcopy(session.get("partner", {}))
    return result


def validate_partner_login():
    try:
        copy_data = copy.deepcopy(request.form)
        payload = {data: copy_data[data] for data in copy_data}
        api_data = requests.get(
            app.config['API_SERVER']['dashboard'] + '/api/partner',
            params=payload
        )
        result_json = api_data.json()
        if api_data.status_code == 200:
            session['partner'] = {}
            session['partner']['partner'] = result_json['result']
            print session['partner']
        return json.dumps(api_data.json()), api_data.status_code
    except Exception, e:
        print e
        return jsonify({'status': 'failure', 'error': str(e)}), 403


def partner_register():
    try:
        form = copy.deepcopy(request.form)
        if request.method == 'POST':
            name = form.get('name', '').strip()
            if not name:
                return jsonify({
                    'status': 'failure',
                    'error': 'Name not provided'}), 403
            if len(name.strip()) < 2:
                return jsonify({
                    'status': 'failure',
                    'error': 'The length of name must be a minimum of 2 characters'}), 403
            tag = form.get('tag', '').strip()
            if not tag:
                return jsonify({
                    'status': 'failure',
                    'error': 'Tag not provided'}), 403
            if len(tag.strip()) < 2 or len(tag.strip()) > 5:
                return jsonify({
                    'status': 'failure',
                    'error': 'The length of tag must be a minimum of 2 characters and maximum of 5 characters'}), 403
            email = form.get('email', '').strip()
            if not email:
                return jsonify({
                    'status': 'failure',
                    'error': 'Email not provided'}), 403

            valid_email = bool(re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email))
            if not valid_email:
                return jsonify({
                    'status': 'failure',
                    'error': 'Given email is invalid, provide a proper email format'}), 403
            phone = form.get('phone', '')
            if not phone:
                return jsonify({
                    'status': 'failure',
                    'error': 'Phone not provided'}), 403
            if (not phone.isdigit()) or (len(phone) != 10):
                return jsonify({'status': 'failure', 'error': 'Phone number must consist of a max of 10 digits'}), 403
            api_data = requests.post(
                app.config['API_SERVER']['dashboard'] + '/api/partner',
                data=form
            )
            return json.dumps(api_data.json()), api_data.status_code
        else:
            return jsonify({'status': 'failure', 'message': 'Request method invalid'}), 200
    except Exception, e:
        print e
        return jsonify({'status': 'failure', 'error': str(e)}), 403


@commonrender('partner/partner_customer.jinja')
def partner_customers():
    try:
        result = copy.deepcopy(session.get("partner", {}))
        partner_id = result.get('partner').get('partner_id', '')
        if partner_id is '':
            return redirect('/partner')
        partner_users = requests.get(
            app.config['API_SERVER']['dashboard'] + '/api/partner/' + partner_id + '/user',
        )
        if partner_users.status_code == 500:
            partner_users = []
        elif partner_users.status_code == 200:
            partner_users = (partner_users.json())['result']
        result.update({'user_list': partner_users})
        print "result.......", result
        return result
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 403


def partner_customer_data(user_id):
    try:
        result = copy.deepcopy(session.get("partner", {}).get("partner", {}))
        partner_id = result.get('partner_id', '')
        if partner_id is '':
            return redirect('/partner')
        partner_users = requests.get(
            app.config['API_SERVER']['dashboard'] + '/api/partner/' + partner_id + '/user/' + user_id,
        )
        result = (partner_users.json())['result']
        return result
    except Exception as e:
        return {'status': 'failure', 'error': str(e)}


def partner_add_customer():
    try:
        result = copy.deepcopy(session.get("partner", {}).get("partner", {}))
        partner_id = result.get('partner_id', '')
        if partner_id is '':
            return redirect('/partner')
        if request.method == 'POST':
            form = copy.deepcopy(request.form)
            name = form.get('name', '').strip()
            if not name:
                return jsonify({
                    'status': 'failure', 
                    'error': 'Name not provided'}), 403
            if len(name.strip()) < 2:
                return jsonify({
                    'status': 'failure', 
                    'error': 'The length of name must be a minimum of 2 characters'}), 403
            email = form.get('email', '').strip()
            if not email:
                return jsonify({
                    'status': 'failure', 
                    'error': 'Email not provided'}), 403

            valid_email = bool(re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email))
            if not valid_email:
                return jsonify({
                    'status': 'failure',
                    'error': 'Given email is invalid, provide a proper email format'}), 403
            phone = form.get('phone', '')
            if not phone:
                return jsonify({
                    'status': 'failure',
                    'error': 'Phone not provided'}), 403
            if (not phone.isdigit()) or (len(phone) != 10):
                return jsonify({'status': 'failure', 'error': 'Phone number must consist of a max of 10 digits'}), 403
            partner_id = result.get('partner_id', '')
            r = requests.post(
                app.config['API_SERVER']['dashboard'] + '/api/partner/' + partner_id + '/user',
                data=form
            )
            print "r....", r.json()
            if r.json()['status'] == 'failure':
                return json.dumps(r.json()), r.status_code
        return jsonify({'status': 'success', 'message': 'User added successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 403


@commonrender('partner/partner_customer_schedule_order.jinja')
def partner_place_order(customer_id=None):
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return redirect("/partner")
    customer_data = usersDAO.get_user(customer_id)
    if not ('customer' in result):
        result['customer'] = {}
    if 'name' in customer_data and customer_data['name']:
        result['customer']['name'] = customer_data['name']
    if 'phone' in customer_data and customer_data['phone']:
        result['customer']['phone'] = customer_data['phone']
    if 'email' in customer_data and customer_data['email']:
        result['customer']['email'] = customer_data['email']
    result.update(itemsDAO.get_all_items())
    result.update({
        "address_list": dict(enumerate(addressDAO.get_user_address(customer_id).get("result"))),
        'customer_id': customer_id
    })
    return result


@commonrender('profile/partner_customer_profile.jinja')
def partner_customer_profile(customer_id=None):
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return redirect("/partner")
    if customer_id:
        result.update(usersDAO.get_user(customer_id))
        address_list = addressDAO.get_user_address(customer_id).get("result")
        result.update({
            "address_list": dict(enumerate(address_list)),
            'customer_id': customer_id
        })
        return result
    else:
        return redirect('/partner/customer/order/' + customer_id)


def partner_logout():
    session.pop('partner')
    return redirect('/partner')


@commonrender('partner/partner_history.jinja')
def partner_get_top():
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return redirect("/partner")
    else:
        partner_id = result.get('partner').get('partner_id')
        partner = result.get('partner')
    res = requests.get(
        app.config['API_SERVER']['dashboard'] + '/api/partner/' + partner_id + '/orders',
    )
    result = (res.json())['result']
    return {'result': result, 'partner': partner}


def partner_submit_order():
    result = copy.deepcopy(session.get("partner", {}))

    if request.method == 'POST':
        if not ('partner' in result):
            return {'status': 'failure', 'error': 'user not logged in.'}, 403
        try:
            # Order Validation Script:
            copy_data = copy.deepcopy(request.form)
            copy_data = copy_data.copy()

            if not copy_data.get('customer_id', ''):
                return jsonify({"status": 'failure', "error": "Please Select a Customer"}), 403

            if not copy_data.get("service", ''):
                return jsonify({"status": 'failure', "error": "Please Select a Service type"}), 403

            if not copy_data.get("address_id"):
                return jsonify({"status": 'failure', "error": "Please Select a address"}), 403
            address = addressDAO.get_address(copy_data.get("address_id"))
            if not address['result'][0]['assigned_hub']:
                return jsonify({"status": 'failure', "error": "Locality not provided in address."}), 403

            if not copy_data.get("pickup_time"):
                return jsonify({"status": 'failure', "error": "Please Select a pick up time"}), 403

            if not compare(copy_data.get("pickup_date_submit", ""), copy_data.get("schedule_date_submit", "")):
                return jsonify({
                    "status": 'failure',
                    "error": "Do you want to interchange pickup and delivery ?!!"
                }), 403

            user_data = usersDAO.get_user(copy_data.get('customer_id', ''))
            if 'phone' in user_data and user_data['phone']:
                copy_data.add('phone', user_data['phone'])

            pickup_schedule = schedulesDAO.base_schedule()
            delivery_schedule = schedulesDAO.base_schedule()

            pickup_schedule["address_id"] = copy_data.get("address_id")
            delivery_schedule["address_id"] = copy_data.get("address_id")

            pickup_schedule["is_pickup"] = True
            delivery_schedule["is_pickup"] = False
            
            try:
                pickup_schedule["schedule_time"] = app.config['TIMESLOTS'][
                    str(copy_data.get("pickup_time"))]
            except KeyError:
                return jsonify({"status": 'failure', "error": "Timeslot doesn't exist."}), 403
            pickup_schedule["schedule_date"] = copy_data.get("pickup_date_submit")
            pickup_schedule["schedule_date_new"] = datetime.strptime(
                copy_data.get("pickup_date_submit"), "%Y/%m/%d")
            
            try:
                delivery_schedule["schedule_time"] = app.config['TIMESLOTS'][
                    str(copy_data.get("schedule_time"))]
            except Exception, e:
                return jsonify({"status": "failure", "error": "Timeslot doesn't exist."}), 403
            if copy_data.getlist("schedule_date_submit")[0] != "":
                delivery_schedule["schedule_date"] = copy_data.getlist(
                    "schedule_date_submit")[0]
                delivery_schedule["schedule_date_new"] = datetime.strptime(
                    copy_data.getlist("schedule_date_submit")[0], "%Y/%m/%d")
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
            
            order_form_data = {'pickup_time': pickup_time,
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
           
            return jsonify({"status": 'success', "order_form_data": order_form_data})
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            log = {
                'event': 'order_session_store',
                'exception': repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                'user_id': session.get("id", None),
                'order_form_data': json.dumps(copy.deepcopy(request.form))
            }
            mongo_logger.exception_logs.insert(log)
            print 'exception is', e
            return jsonify({'status': 'failure', 'error': 'exception while doing.'}), 403
        return jsonify(result)
    else:
        return jsonify({'status': 'failure', 'error': 'unauthorized access.'}), 403


def compare(pickup, delivery):
    return True
    if int(delivery[-4:]) >= int(pickup[-4:]):
        return True
    else:
        return False


def partner_coupon_verify():
    result = copy.deepcopy(session.get("partner", {}))
    if request.method == 'POST':
        if not ('partner' in result):
            return {'status': 'failure', 'error': 'user not logged in.'}, 403
        copy_data = copy.deepcopy(request.form)
        if not copy_data.get('customer_id', ''):
            return jsonify({"status": 'failure', "error": "Please Select a Customer"}), 403

        pickup_schedule = schedulesDAO.base_schedule()
        delivery_schedule = schedulesDAO.base_schedule()

        pickup_schedule["address_id"] = copy_data["address_id"]
        delivery_schedule["address_id"] = copy_data["address_id"]

        pickup_schedule["is_pickup"] = True
        delivery_schedule["is_pickup"] = False
        try:
            pickup_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["pickup_time"])]
        except KeyError:
            return jsonify({"status": 'failure', "error": "Pickup Schedule Timeslot doesn't exist."}), 403
        pickup_schedule["schedule_date"] = copy_data["pickup_date_submit"]
        pickup_schedule["schedule_date_new"] = copy_data["pickup_date_submit"]
        try:
            delivery_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["schedule_time"])]
        except Exception, e:
            return jsonify({"status": 'failure', "error": "Delivery Schedule Timeslot doesn't exist."}), 403
        if copy_data["schedule_date_submit"] != "":
            delivery_schedule["schedule_date"] = copy_data["schedule_date_submit"]
            delivery_schedule["schedule_date_new"] = copy_data["schedule_date_submit"]
        else:
            copy_data["schedule_date_submit"]
        print "2"
        coupon_name = ''
        service_type = ''
        if 'service' in copy_data and copy_data['service']:
            service_type = copy_data['service']
        if 'partner_customer_coupon' in copy_data and copy_data['partner_customer_coupon']:
            coupon_name = copy_data.get("partner_customer_coupon").lower().strip()
        user_id = copy_data.get('customer_id', '')
        print "3"
        if coupon_name:
            if service_type:
                try:
                    payload_data = {'user_id': user_id, 'coupon': coupon_name, 'service':service_type}
                    url = config.API_SERVER['private_dashboard'] + "/api/couponverify/coupon"
                    r = requests.post(url, data=payload_data)
                    coupon_data = r.json()
                    # Must get Terms and conditions here and show it on notification
                    if coupon_data['status'] == 'success':
                        return jsonify({"status": 'success', "terms": coupon_data['terms']})
                    else:
                        return jsonify({"status": 'failure', "error": coupon_data['error']}), 403

                    return jsonify(result)
                except Exception, e:
                    return jsonify({"status": 'failure', "error": "Some error occured. Contact customer support."}), 403
        else:
            return jsonify({"status": 'failure', "error": "Some error occured. Contact customer support."}), 403
    else:
        try:
            result.update(addressDAO.get_user_address(session.get("id")))
        except Exception, e:
            result = []
    return jsonify(result)


def partner_complete_order():
    result = copy.deepcopy(session.get("partner", {}))
    if request.method == 'POST':
        if not ('partner' in result):
            return {'status': 'failure', 'error': 'user not logged in.'}, 403
        try:
            copy_data = copy.deepcopy(request.form)

            if not copy_data.get('customer_id', ''):
                return jsonify({"status": 'failure', "error": "Please Select a Customer"}), 403

            data = ordersDAO.base_order()

            pickup_schedule = schedulesDAO.base_schedule()
            delivery_schedule = schedulesDAO.base_schedule()

            pickup_schedule["address_id"] = copy_data["address_id"]
            delivery_schedule["address_id"] = copy_data["address_id"]
            pickup_schedule["is_pickup"] = True
            delivery_schedule["is_pickup"] = False
            try:
                pickup_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["pickup_time"])]
            except KeyError:
                return jsonify({"status": 'failure', "error": "Pickup Schedule Timeslot doesn't exist."}), 403

            pickup_schedule["schedule_date"] = copy_data["pickup_date_submit"]
            pickup_schedule["schedule_date_new"] = datetime.strptime(pickup_schedule["schedule_date"], "%Y/%m/%d")

            try:
                delivery_schedule["schedule_time"] = app.config['TIMESLOTS'][str(copy_data["schedule_time"])]
            except Exception, e:
                return jsonify({"status": 'failure', "error": "Delivery Schedule Timeslot doesn't exist."}), 403

            if copy_data["schedule_date_submit"] != "":
                delivery_schedule["schedule_date"] = copy_data["schedule_date_submit"]
                delivery_schedule["schedule_date_new"] = datetime.strptime(delivery_schedule["schedule_date"], "%Y/%m/%d")
            coupon_name = ""
            service_type = copy_data['service']
            user_order_coupon_id = ""
            user_id = copy_data.get('customer_id', '')
            is_coupon_valid = False

            if 'partner_customer_coupon' in copy_data and copy_data['partner_customer_coupon']:
                coupon_name = copy_data.get("partner_customer_coupon").lower().strip()
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
                        is_coupon_valid = False
                        if 'message' in result_data and result_data['message']:
                            return jsonify({"status": 'failure', "error": result_data['message']}), 403
                        else:
                            return jsonify({"status": 'failure', "error": result_data['message']}), 403

                except Exception, e:
                    print e
                    return jsonify({"status": 'failure', "error": "Failed while placing order using coupon"}), 403

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
            data["user_id"] = copy_data.get('customer_id')

            user_data = usersDAO.get_user(copy_data.get('customer_id'))
            data["partner_id"] = user_data.get('partner').get('id')
            data["phone"] = user_data.get('phone', None)

            data["type"] = copy_data["washtypes"].split(",")

            print "data....", data
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
                except Exception, e:
                    print e
            data["order_id"] = 'EX' + data["order_id"] if data["service_type"] == "express" else data["order_id"]
            order_id = ordersDAO.submit_order(data)
            print "order_id......", order_id

            # below code to update order column in user order coupon table
            try:
                url = config.API_SERVER['private_dashboard'] + "/api/couponverify"
                payload = {'method': 'update', 'uoc_str_id': user_order_coupon_id, 'order': order_id}
                r = requests.put(url, data=payload)
            except Exception, e:
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

        is_sms_block = result.get('partner').get('is_sms_block')
        if order_id > 0:
            partner_id = result.get('partner').get('partner_id')
            result = {"status": 'success', "order": {"id": order_id}}
            if 'email' in user_data:
                emails.email_order_placed.delay({
                    "order_id": str(order_id),
                    "email": user_data['email'],
                    "name": user_data['name'],
                    "service_type": data["service_type"]})
            print "sms block....", is_sms_block, type(is_sms_block)
            # SMS BLOCKING
            if not is_sms_block:
                sms.sms_order_placed.delay({
                    "order_id": str(order_id),
                    "name": user_data['name']})
        else:
            return jsonify({"status": 'failure', "error": "Failed to order"}), 403

        # Assign hub for the order asyncronously by using its address
        try:
            arequests.put(app.config['API_SERVER']['private_dashboard'] + "/api/address/" + data["address_id"], data={'refresh_hub': 'true'})
        except Exception, e:
            pass
        return jsonify(result)
    else:
        return jsonify({'status': 'failure', 'error': 'unauthorized access.'}), 403


def partner_get_order(customer_id=None, order_id=None):
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return redirect("/partner")
    order = ordersDAO.get_order(order_id)
    if order.get("status", 1) == 5:
        return redirect("/partner/getreceipt/" + str(customer_id) + "/" + str(order_id))
    else:
        return redirect("/partner/getstatus/" + str(customer_id) + "/" + str(order_id))


@commonrender('order/order_history/partner_customer_order_receipt.jinja')
def partner_get_receipt(customer_id=None, order_id=None):
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return redirect("/partner")
    result.update(ordersDAO.get_order(order_id))
    return result


@commonrender('order/partner_customer_order_status.jinja')
def partner_get_status(customer_id=None, order_id=None):
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return redirect("/partner")
    data_form = dict(copy.deepcopy(request.args)) or {'transaction_status': '', 'transaction_message': ''}
    if customer_id:
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
        result['customer_id'] = customer_id
        if 'coupon' in order and 'name' in order['coupon']:
            try:
                url = config.API_SERVER['private_dashboard'] \
                    + "/api/couponverify/order/" + order_id
                r = requests.get(url)
                coupon_data = r.json()
                print "coupon_data,....", coupon_data
                if coupon_data['status'] == 'success':
                    result['coupon_applied'] = coupon_data
                else:
                    result['coupon_applied'] = coupon_data
            except Exception, e:
                print e
        else:
            result['coupon_applied'] = {'status': 'failure'}
        print "result,....", result
        return result
    else:
        return redirect("/partner/customer")


def partner_cancel_order(customer_id=None):
    order_id = request.args.get("order_id", 0)
    result = session.get("partner")
    if not ('partner' in result):
        return redirect("/partner")
    result1 = ordersDAO.order_status_update(order_id, 'order_cancelled')
    
    partner_id = result.get('partner').get('partner_id')
    is_sms_block = result.get('partner').get('is_sms_block')

    if result1:
        result = {"status": 'success', "order": {"id": order_id}}
        try:
            url = config.API_SERVER['private_dashboard'] + "/api/couponverify"
            payload = {'method': 'delete', 'order': order_id}
            r = requests.put(url, data=payload)
        except Exception, e:
            print e
        user = usersDAO.get_user_by_order_id(order_id)
        print "user......", user
        emails.email_order_cancelled.delay(
            {"order_id": str(order_id),
                "email": user["email"],
                "name": user["name"]})

        order_det = ordersDAO.get_order(order_id)

        if not is_sms_block:
            sms.sms_order_cancelled.delay({
                "order_id": str(order_id),
                "email": user["email"],
                "name": user["name"]})
        return jsonify(result)
    else:
        return jsonify({"status": 'failure', "error": "Failed to  Cancel order"}), 403


@commonrender('partner/partner_help.jinja')
def partner_help():
    result = copy.deepcopy(session.get("partner", {}))
    return result


@commonrender('partner/partner_customer.jinja')
def partner_search_customer(search=None):
    result = copy.deepcopy(session.get("partner", {}))
    if not ('partner' in result):
        return jsonify({'status': 'failure', 'error': 'Failed while getting partner details'}), 403
    # copy_data = copy.deepcopy(request.form)
    partner_id = result.get('partner').get('partner_id')
    # print "copy_data....", copy_data
    # print "email....", copy_data.get('search')
    is_phone = False
    if search.isdigit():
        is_phone = True
    try:
        url = config.API_SERVER['private_dashboard'] + "/api/partner/search/" + partner_id
        if is_phone:
            payload = {'phone': search}
        else:
            payload = {'email': search}
        print "payload...", payload
        r = requests.get(url, data=payload)
        if r.status_code == 500:
            partner_users = []
        elif r.status_code == 200:
            partner_users = (r.json())['result']
        else:
            redirect('/partner/customer')
        result.update({'user_list': partner_users})
        result.update({'in_search': True})
        print "result.......", result
        return result
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 403

