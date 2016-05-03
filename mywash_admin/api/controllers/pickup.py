from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
import re
from api.models import Employee as EmployeeModel
from api.controllers.misc import PickupSheetInfo
import json
from mywash_admin.lib import emails
from api.controllers.employees import Employee
from mywash_admin.lib.loggers import MongoLogger
from api.models import MywashHub


PICKUP_TYPES = [
    'order',
    'missed',
    'rescheduled'
]

db = app.config['MONGO_CLIENT']['dealsup']

SMS_LOGGER = MongoLogger('mywash_logs', 'sms_logs')
LOGGER = MongoLogger('mywash_logs', 'general_logs')

HUBS = {}
try:
    hubs = MywashHub.query.all()
    for hub in hubs:
        HUBS[hub.id] = {
            'str_id': hub.str_id,
            'short': hub.data['short'],
            'name': hub.data['name']
        }
except Exception, e:
    raise e


class PickupDate(Resource):
    '''
    Given the date a list of pickups are provided.
    '''
    def get(self, pickup_type=None, date=None, time=None):
        if pickup_type and pickup_type not in PICKUP_TYPES:
            return {'error': '"%s" is a wrong argument. Must be either "order", "missed" or "rescheduled"'}, 404
        current_datetime = None
        current_date = None
        current_time = None

        if date:
            try:
                current_datetime = datetime.strptime(date, "%Y-%m-%d")
            except Exception, e:
                return {'error': 'Format of date must be "yyyy-mm-dd"'}, 404

            # if app.config['DEBUG']:
            #     current_datetime = datetime.strptime("2015/01/02 9am", "%Y/%m/%d %I%p")
            current_date = current_datetime.date().strftime("%Y/%m/%d")
            if time:
                current_time = datetime.strptime(time, "%H-%M").time()

        pickup_ids = []
        pickup_items = {}
        assignment_ids = {}

        if current_date:
            pickups = db.schedules.find({'schedule_date': current_date, 'is_pickup': True, 'is_active': True})
        else:
            pickups = db.schedules.find({'is_pickup': True, 'is_active': True})

        for item in pickups:
            if not item['schedule_time'].strip():
                item['schedule_time'] = "6am - 8am"

            schedule_time_floor = item['schedule_time'].split("-")[0].strip()
            schedule_time_ceil = item['schedule_time'].split("-")[-1].strip()
            try:
                schedule_time_floor = datetime.strptime(schedule_time_floor, "%I%p").time()
            except ValueError, e:
                schedule_time_floor = datetime.strptime(self.__repair_time(schedule_time_floor, schedule_time_ceil), "%I%p").time()

            try:
                schedule_time_ceil = datetime.strptime(schedule_time_ceil, "%I%p").time()
            except Exception, e:
                schedule_time_ceil = datetime.strptime(self.__repair_time(schedule_time_ceil, schedule_time_floor), "%I%p").time()

            if current_time:
                if pickup_type == 'order':
                    if current_time < schedule_time_ceil:
                        continue
                elif pickup_type == 'missed':
                    if current_time >= schedule_time_ceil:
                        continue

            pickup_ids.append(item['_id'])
            item['schedule_time_ceil'] = int(schedule_time_floor.strftime("%H")) + int(schedule_time_ceil.strftime("%H"))
            pickup_items[str(item['_id'])] = item
            if 'assigned_to' in item:
                assignment_ids[str(item['_id'])] = item['assigned_to']

        employees = []
        if assignment_ids:
            try:
                employees = EmployeeModel.query.filter(EmployeeModel.str_id.in_(tuple(assignment_ids.values())))
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500

        employee_dict = {}
        for employee in employees:
            employee_dict[employee.str_id] = {
                'name': employee.data['name'],
                'str_id': employee.str_id,
                'emp_id': "%.5d" % employee.id
            }

        # print pickup_ids
        order_items = []
        user_ids = []
        try:
            orders = db.orders.find({
                'pickup_id': {'$in': pickup_ids},
                    'status': {
                        '$in': [1, 2, 'order_placed', 'pickup_progress', 'pickup_failed', 'pickup_success']
                    }
                }, {'order_id': 1, 'user_id': 1, 'total_price': 1,
                'pickup_id': 1, 'status': 1, 'order_items': 1, 'is_paid': 1,
                'pickup_sheet_printed': 1, 'address_id': 1, 'phone': 1,'service_type':1}
            )

        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        address_ids = []
        for order in orders:
            item_dict = {}
            item_dict['status'] = order['status']
            item_dict['phone'] = order.get('phone', None)
            item_dict['assigned_to'] = order['assigned_to'] if 'assigned_to' in order and order['assigned_to'] else None
            item_dict['pickup_sheet_printed'] = order['pickup_sheet_printed'] if 'pickup_sheet_printed' in order else False
            item_dict['order_id'] = str(order['_id'])
            item_dict['is_paid'] = order['is_paid'] if 'is_paid' in order else False
            item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
            item_dict['user_id'] = order['user_id']
            item_dict['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
            item_dict['address_id'] = order['address_id']
            item_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
            item_dict['schedule_time'] = pickup_items[str(order['pickup_id'])]['schedule_time_ceil']
            item_dict['schedule_time_range'] = pickup_items[str(order['pickup_id'])]['schedule_time']
            order_items.append(item_dict)
            user_ids.append(order['user_id'])
           # print(order_items[item_dict['service_type']])
            try:
                address_ids.append(bson.ObjectId(order['address_id']))
            except Exception, e:
                pass
            if str(order['pickup_id']) in assignment_ids and assignment_ids[str(order['pickup_id'])]  in employee_dict:
                item_dict['assigned_to'] = employee_dict[assignment_ids[str(order['pickup_id'])]]

        users_dict = {}
        for user in db.users.find({'user_id': {'$in': user_ids}}, {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1}):
            user['_id'] = str(user['_id'])
            users_dict[user['user_id']] = user

        address_dict = {}
        for address in db.addresses.find({'_id': {'$in': address_ids}}):
            if 'assigned_hub' in address:
                address_dict[str(address['_id'])] = int(address['assigned_hub'])

        for order in order_items:
            order['user_info'] = users_dict[order['user_id']]
            if order['address_id'] in address_dict:
                order['hub'] = HUBS[address_dict[order['address_id']]]
            else:
                order['hub'] = HUBS[1]

        return jsonify({'data': order_items})

    def __repair_time(self, impure, pure):
        noon = 'am' if 'am' in pure else 'pm'
        lis = re.findall(r'\d', impure)
        int_time = int("".join(lis))
        return str(int_time) + "am" if int_time < 12 and noon == "pm" else str(int_time) + "pm"

    def put(self):
        form = copy.deepcopy(request.form)
        if 'order_id' not in form:
            return {'status': 'failure', 'error': "order id not found."}, 403

        order = db.orders.find_one({'_id': bson.ObjectId(form['order_id'])})
        now = datetime.utcnow()
        if 'date' in form and 'time' in form:
            try:
                db.schedules.update({
                    '_id': order['pickup_id']
                }, {
                    '$set': {
                        'schedule_date': form['date'],
                        'schedule_time': form['time'],
                        'updated-time': now
                    }
                })
                LOGGER.info(
                    event='pickup_reschedule',
                    order_id=str(order['_id']),
                )
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
        elif 'date' in form or 'time' in form:
            return {'status': 'failure', 'error': 'Date and timeslot both are required.'}, 403

        if 'assign_to' in form:
            try:
                db.schedules.update({
                    '_id': order['pickup_id']
                }, {
                    '$set': {
                        'assigned_to': form['assign_to'],
                        'updated-time': now
                    }
                })
                LOGGER.info(
                    event='pickup_assigned_to',
                    order_id=str(order['_id']),
                    assigned_to=form['assign_to']
                )
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500

            try:
                db.orders.update({'_id': bson.ObjectId(form['order_id'])}, {
                    '$set': {
                        'status': "pickup_progress"
                    }
                })
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500

            try:
                employee = Employee()
                employee = json.loads(employee.get(emp_id=form['assign_to']).response[0])['data'][0]
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500

            info = PickupSheetInfo()
            data = json.loads(info.get(order_ids=json.dumps([form['order_id']])).response[0])['data'][0]
            subs = {
                'oid': data['real_order_id'],
                'name': data['user']['name'],
                'phone': data['user']['phone'],
                'pickup_date': data['schedules'][0]['pickup']['schedule_date'],
                'pickup_time': data['schedules'][0]['pickup']['schedule_time'],
                'flat_no': data['address']['apartment_number'],
                'address_1': data['address']['address_1'],
                'address_2': data['address']['address_2'],
                'locality': data['address']['locality']['map_string'] if 'locality' in data['address'] else ""
            }
            message = u"""Oid-#%(oid)s
%(name)s
Ph-%(phone)s
Pickup-%(pickup_date)s,%(pickup_time)s
Addr-%(flat_no)s,%(address_1)s,%(address_2)s
Loc-%(locality)s
""" % subs

            status_info = emails.mywash_order_transactional_sms(
                employee['data']['phone'][0],
                message,
                order.get('partner_id', None)
            )

            # status_info = [v for v in status_info.collect()][0][1]
            # print "emp_id ", form["assign_to"], "...order_id..", subs["oid"]
            notification_status_info = emails.notification_alert_agent_pickup(
                emp_id=form['assign_to'], order_id=subs['oid']
            )
            # if isinstance(notification_status_info, tuple):
            #     print "error status_code:", notification_status_info[1], " message: ", notification_status_info[0]['error']
            # print "notification_status_info", notification_status_info, ".............."
            # if status_info:
            #     SMS_LOGGER.info(
            #         "pickup assignment sms",
            #         event='pickup_assignment_sms',
            #         sms_to_name=employee['data']['name'],
            #         sms_to_number=employee['data']['phone'][0],
            #         order_id=order['order_id']
            #     )
            # else:
            #     SMS_LOGGER.error(
            #         "pickup assignment sms",
            #         event='pickup_assignment_sms',
            #         sms_to_name=employee['data']['name'],
            #         sms_to_number=employee['data']['phone'][0],
            #         order_id=order['order_id']
            #     )
            
            # customer_sms = "%s, your order (#%s) has been assigned to our pickup agent %s (%s) for the timeslot %s." % (
            #     data['user']['name'],
            #     data['real_order_id'],
            #     employee['data']['name'],
            #     employee['data']['phone'][0],
            #     data['schedules'][0]['pickup']['schedule_time'].replace(" ", '')
            # )

            # if app.config['DEBUG']:
            #     print emails.mywash_order_transactional_sms(employee['data']['phone'][0], "Hi %s Thank you." % customer_sms)
            # else:
            #     print emails.mywash_order_transactional_sms(data['user']['phone'], "Hi %s Thank you." % customer_sms)

        return {'status': 'success'}
