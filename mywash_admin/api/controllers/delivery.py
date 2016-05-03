from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
import json
from api.models import MywashHub
from api.controllers.employees import Employee
from mywash_admin.lib.loggers import MongoLogger
from mywash_admin.lib import emails
from api.models import Employee as EmployeeModel
from api.controllers.misc import PickupSheetInfo
import re
from mywash_admin.lib import emails
from api.controllers.employees import Employee


DELIVERY_TYPES = [
    'order',
    'missed',
    'rescheduled'
]

db = app.config['MONGO_CLIENT']['dealsup']

LOGGER = MongoLogger('mywash_logs', 'general_logs')

HUBS = {}
try:
    hubs = MywashHub.query.all()
    for hub in hubs:
        HUBS[hub.id] = {
            'short': hub.data['short'],
            'name': hub.data['name']
        }
except Exception, e:
    raise e


class DeliveryDate(Resource):
    '''
    Given the date a list of deliverys are provided.
    '''
    def get(self, delivery_type=None, date=None, time=None):
        if delivery_type and delivery_type not in DELIVERY_TYPES:
            return {'error': '"%s" is a wrong argument. Must be either "order", "missed" or "rescheduled"'}, 404
        current_datetime = None
        current_date = None
        current_time = None
        assignment_ids = {}

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
        
        delivery_ids = []
        delivery_items = {}

        if current_date:
            deliverys = db.schedules.find({'schedule_date': current_date, 'is_pickup': False, 'is_active': True})
        else:
            deliverys = db.schedules.find({'is_pickup': False, 'is_active': True})

        for item in deliverys:
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
                if delivery_type == 'order':
                    if current_time < schedule_time_ceil:
                        continue
                elif delivery_type == 'missed':
                    if current_time >= schedule_time_ceil:
                        continue

            delivery_ids.append(item['_id'])
            item['schedule_time_ceil'] = int(schedule_time_floor.strftime("%H")) + int(schedule_time_ceil.strftime("%H"))
            delivery_items[str(item['_id'])] = item
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

        # print delivery_ids
        order_items = []
        user_ids = []
        try:
            orders = db.orders.find({
                'delivery_id': {'$in': delivery_ids},
                'status': {
                        '$nin': [4, 5, 6, 'clothes_delivered', 'order_cancelled', 'order_rejected']
                    }
                }, {'order_id': 1, 'user_id': 1, 'total_price': 1, 'delivery_id': 1, 'status': 1, 'order_items': 1,'phone': 1,'service_type':1,'cash_collected': 1,'is_paid':1, 'address_id': 1}
            )
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        address_ids = []        

        for order in orders:
            if 'is_paid' in order:
                if isinstance(order['is_paid'], bool):
                    order['is_paid'] = 'paid' if order['is_paid'] else 'not_paid'       

            item_dict = {}
            item_dict['status'] = order['status']
            item_dict['assigned_to'] = order['assigned_to'] if 'assigned_to' in order and order['assigned_to'] else None
            item_dict['order_id'] = str(order['_id'])
            item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
            item_dict['user_id'] = order['user_id']
            item_dict['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
            item_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
            item_dict['schedule_time'] = delivery_items[str(order['delivery_id'])]['schedule_time_ceil']
            item_dict['schedule_time_range'] = delivery_items[str(order['delivery_id'])]['schedule_time']
            item_dict['phone'] = order.get('phone', None)
            item_dict['is_paid'] =  order['is_paid'] if 'is_paid' in order else 'not_paid'
            item_dict['cash_collected'] = order.get('cash_collected', 0)
            item_dict['address_id'] = order.get('address_id', None)

            order_items.append(item_dict)
            user_ids.append(order['user_id'])
            try:
                address_ids.append(bson.ObjectId(order['address_id']))
            except Exception, e:
                pass
            if str(order['delivery_id']) in assignment_ids and assignment_ids[str(order['delivery_id'])]  in employee_dict:
                item_dict['assigned_to'] = employee_dict[assignment_ids[str(order['delivery_id'])]]

        users_dict = {}
        for user in db.users.find({'user_id': {'$in': user_ids}}, {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1}):
            user['_id'] = str(user['_id'])
            users_dict[user['user_id']] = user

        address_dict = {}
        for address in db.addresses.find({'_id': {'$in': address_ids}}):
            if 'assigned_hub' in address:
                address_dict[str(address['_id'])] = int(address['assigned_hub'])

        for order in order_items:
            order['user_info'] = users_dict.get(order['user_id'], {})
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
        print form
        order = db.orders.find_one({'_id': bson.ObjectId(form['order_id'])})
        now = datetime.utcnow()
        if 'date' in form and 'time' in form:
            try:
                db.schedules.update({
                    '_id': order['delivery_id']
                }, {
                    '$set': {
                        'schedule_date': form['date'],
                        'schedule_time': form['time'],
                        'updated-time': now
                    }
                })
                LOGGER.info(
                    event='delivery_reschedule',
                    order_id=str(order['_id']),
                )
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
        elif 'date' in form or 'time' in form:
            return {'status': 'failure', 'error': 'Date and timeslot both are required.'}, 403
            
        elif 'assign_to' in form:
            try:
                db.schedules.update({
                    '_id': order['delivery_id']
                }, {
                    '$set': {
                        'assigned_to': form['assign_to'],
                        'updated-time': now
                    }
                })
                LOGGER.info(
                    event='delivery_assigned_to',
                    order_id=str(order['_id']),
                    assigned_to=form['assign_to']
                )
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500

            try:
                db.orders.update({'_id': bson.ObjectId(form['order_id'])}, {
                    '$set': {
                        'status': "delivery_progress" 
                    }
                })
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500

            info = PickupSheetInfo()
            data = json.loads(info.get(order_ids=json.dumps([form['order_id']])).response[0])['data'][0]
            subs = {
                'oid': data['real_order_id'],
                'name': data['user']['name'],
                'phone': data['user']['phone'],
                'delivery_date': data['schedules'][0]['delivery']['schedule_date'],
                'delivery_time': data['schedules'][0]['delivery']['schedule_time'],
                'flat_no': data['address']['apartment_number'],
                'address_1': data['address']['address_1'],
                'address_2': data['address']['address_2']
            }
            
            emails.notification_alert_agent_delivery(
                emp_id=form['assign_to'], order_id=subs['oid']
            )

#             try:
#                 employee = Employee()
#                 employee = json.loads(employee.get(emp_id=form['assign_to']).response[0])['data'][0]
#             except Exception, e:
#                 return {'status': 'failure', 'error': 'db error.'}, 500

#             info = PickupSheetInfo()
#             data = json.loads(info.get(order_ids=json.dumps([form['order_id']])).response[0])['data'][0]
#             subs = {
#                 'oid': data['real_order_id'],
#                 'name': data['user']['name'],
#                 'phone': data['user']['phone'],
#                 'delivery_date': data['schedules'][0]['delivery']['schedule_date'],
#                 'delivery_time': data['schedules'][0]['delivery']['schedule_time'],
#                 'flat_no': data['address']['apartment_number'],
#                 'address_1': data['address']['address_1'],
#                 'address_2': data['address']['address_2']
#             }
#             message = """Oid- #%(oid)s
# %(name)s
# Ph- %(phone)s
# Delivery- %(delivery_date)s, %(delivery_time)s
# Addr- %(flat_no)s, %(address_1)s, %(address_2)s""" % subs
#             status_info = emails.mywash_order_transactional_sms(employee['data']['phone'][0], message)

#             if status_info:
#                 LOGGER.info(
#                     "delivery assignment sms",
#                     sms_to_name=employee['data']['name'],
#                     sms_to_number=employee['data']['phone'][0],
#                     order_id=order['order_id']
#                 )
#             else:
#                 LOGGER.error(
#                     "delivery assignment sms",
#                     sms_to_name=employee['data']['name'],
#                     sms_to_number=employee['data']['phone'][0],
#                     order_id=order['order_id']
#                 )
#             customer_sms = "%s, your order (#%s) has been assigned to our pickup agent %s (%s) for the timeslot %s." % (
#                 data['user']['name'],
#                 data['real_order_id'],
#                 employee['data']['name'],
#                 employee['data']['phone'][0],
#                 data['schedules'][0]['pickup']['schedule_time'].replace(" ", '')
#             )

#             if app.config['DEBUG']:
#                 emails.mywash_order_transactional_sms(employee['data']['phone'][0], customer_sms)
#             else:
#                 emails.mywash_order_transactional_sms(data['user']['phone'], "Hi %s Thank you." % customer_sms)

        return {'status': 'success'}
