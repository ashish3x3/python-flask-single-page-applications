# import calendar
# import geocoder
import datetime
import requests
import math

from collections import OrderedDict
from bson.objectid import ObjectId
from flask.ext.restful import Resource
from flask import jsonify

# from mywash_admin import app, db as pgdb
from mywash_admin import settings
from mywash_admin import app
from mywash_admin.lib import utils

db = app.config['MONGO_CLIENT']['dealsup']


class DummyreyReport(Resource):
    def get(self):
        try:
            orders = db.orders.find({
                'created_date': {
                    '$gte': datetime.datetime.strptime('2014-10-19', '%Y-%m-%d'),
                    '$lt': datetime.datetime.strptime(utils.get_current_time(), '%Y-%m-%d %H:%M:%S')
                }
            })
            user_ids = []
            user_dict = {}
            address_ids = []
            schedule_ids = []
            order_list = []
            for order in orders:
                order_dict = {}
                user_ids.append(order['user_id'])
                schedule_ids.extend([order['pickup_id'], order['delivery_id']])
                address_ids.append(ObjectId(order['address_id']))
                user_dict[order['user_id']] = {
                    'name': None,
                    'email': None,
                }
                order_dict['order_id'] = order['order_id'] if 'order_id' in order and order['order_id'] else str(order['_id'])
                order_dict['name'] = order['user_id']
                order_dict['email'] = order['user_id']
                order_dict['phone'] = order['phone']
                order_dict['status'] = settings.DEPRECATED_STATUS_MAP[order['status']] if type(order['status']) == int else order['status']
                order_dict['pickup_date'] = str(order['pickup_id'])
                order_dict['delivery_date'] = str(order['delivery_id'])
                order_dict['phone'] = order['phone']
                order_dict['hub'] = order['address_id']
                order_dict['type'] = ','.join(order['type']) if type(order['type']) == list else order['type']
                order_dict['order_creation'] = str(order['created_date'].date())
                order_dict['sub_total_price'] = order['sub_total_price'] if 'sub_total_price' in order else 'NA'
                if 'discount' in order and 'amount' in order['discount']:
                    order_dict['discount'] = order['discount']['amount']
                elif 'discount' in order and 'total' in order['discount']:
                    order_dict['discount'] = order['discount']['total']
                else:
                    order_dict['discount'] = 'NA'
                order_dict['service_tax'] = order['service_tax']['amount'] if 'service_tax' in order else 'NA'
                order_dict['total_price'] = order['total_price'] if 'total_price' in order else 'NA'
                order_dict['cash_collected'] = order['cash_collected'] if 'cash_collected' in order else 'NA'
                order_list.append(order_dict)
            addresses = db.addresses.find({'_id': {'$in': address_ids}})
            address_dict = {}
            for address in addresses:
                try:
                    address['_id'] = str(address['_id'])
                    address_dict[address['_id']] = 'MRT' if 'assigned_hub' in address and address['assigned_hub'] == 2 else 'ANY'
                except Exception as e:
                    print address
                    return {'error': e, 'stataus': 'failure'}, 403
            users = db.users.find({'user_id': {'$in': user_ids}})
            schedule_dict = {str(schedule['_id']): schedule for schedule in db.schedules.find({'_id': {'$in': schedule_ids}})}
            for user in users:
                user_dict[user['user_id']]['name'] = user['name'] if 'name' in user and user['name'] else 'NA'
                user_dict[user['user_id']]['email'] = user['email'] if 'email' in user and user['email'] else 'NA'
            for order in order_list:
                try:
                    order['name'] = user_dict[order['name']]['name'].encode('ascii', 'ignore').decode('ascii')
                    order['email'] = user_dict[order['email']]['email'].encode('ascii', 'ignore').decode('ascii')
                    order['pickup_date'] = schedule_dict[order['pickup_date']]['schedule_date']
                    order['delivery_date'] = schedule_dict[order['delivery_date']]['schedule_date']
                    order['hub'] = address_dict[order['hub']]
                except Exception as e:
                    print e, order
            return jsonify({'data': order_list})
        except Exception as e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 403


class AuditReport(Resource):
    def get(self, date, order_type):
        try:
            schedule_query = {'is_active': True, 'schedule_date': date.replace('-', '/')}
            if order_type == 'pickup':
                schedule_query['is_pickup'] = True
            elif order_type == 'delivery':
                schedule_query['is_pickup'] = False
            else:
                return {'status': 'failure', 'error': 'Invalid order type'}, 403
            schedules = db.schedules.find(schedule_query)
            schedule_ids = []
            address_ids = []
            schedule_orders = {}
            for schedule in schedules:
                schedule_ids.append(schedule['_id'])
                try:
                    address_ids.append(ObjectId(schedule['address_id']))
                except Exception as e:
                    return {'status': 'failure', 'error': 'Address object id error'}
                schedule_orders[schedule['_id']] = schedule
            addresses = db.addresses.find({'_id': {'$in': address_ids}})
            address_dict = {}
            for address in addresses:
                address['_id'] = str(address['_id'])
                if 'assigned_hub' in address:
                    address_dict[address['_id']] = 'Hoodi' if address['assigned_hub'] == 2 else 'Anepalya'
                elif 'locality' in address and 'map_string' in address['locality']:
                    address_dict[address['_id']] = address['locality']['map_string']
                # if 'locality' in address and 'map_string' in address['locality'] and 'assigned_hub' in address:
                #     address['assigned_hub'] = 'HOODI' if address['assigned_hub'] == 2 else 'ANEPALYA'
                #     address_dict[address['_id']] = address['assigned_hub'] + '-' + address['locality']['map_string']
                else:
                    address_details = ""
                    if address['apartment_number']:
                        address['apartment_number'] = address['apartment_number'].encode('ascii', 'ignore').decode('ascii')
                        address_details += address['apartment_number'] + '\n'
                    if address['address_1']:
                        address['address_1'] = address['address_1'].encode('ascii', 'ignore').decode('ascii')
                        address_details += address['address_1'] + '\n'
                    if address['address_2']:
                        address['address_2'] = address['address_2'].encode('ascii', 'ignore').decode('ascii')
                        address_details += address['address_2']
                    address_dict[address['_id']] = address_details
            order_query = {'status': {'$nin': [5, 6, 'order_cancelled', 'order_rejected']}}
            if order_type == 'pickup':
                order_query['pickup_id'] = {'$in': schedule_ids}
            elif order_type == 'delivery':
                order_query['delivery_id'] = {'$in': schedule_ids}
            orders = db.orders.find(order_query)
            user_ids = []
            order_list = []
            for order in orders:
                try:
                    order_dict = {}
                    user_ids.append(order['user_id'])
                    order_dict['hub'] = address_dict[order['address_id']].encode('ascii', 'ignore').decode('ascii')
                    order_dict['phone'] = order['phone']
                    order_dict['name'] = order['user_id']
                    order_dict['order_id'] = order['order_id'] if 'order_id' in order and order['order_id'] else str(order['_id'])
                    order_dict['status'] = order['status']
                    order_dict['service_type'] = 'express' if 'service_type' in order and order['service_type'] == 'express' else 'regular'
                    order_dict['schedule_date'] = schedule_orders[order[order_type + '_id']]['schedule_date']
                    order_dict['schedule_time'] = schedule_orders[order[order_type + '_id']]['schedule_time']
                    order_dict['type'] = ','.join(order['type']) if type(order['type']) == list else order['type']
                    str_id = None
                    try:
                        if 'failure_reason' in order and order['failure_reason'][order_type] is not None:
                            str_id = order['failure_reason'][order_type]
                            reason = requests.get('http://54.169.157.52/api/failurereason/' + str_id).json()['data'][0]['reason']
                            # reason = Reason.query.filter(Reason.str_id==str_id).first().data['reason']
                            order_dict['reason'] = reason.encode('ascii', 'ignore').decode('ascii') if reason is not None else None
                        else:
                            order_dict['reason'] = 'None'
                    except Exception as e:
                        print str(e), str_id
                        pass
                    if order_type == 'delivery':
                        order_dict['sub_total_price'] = order['sub_total_price'] if 'sub_total_price' in order else 0
                        if 'discount' in order and 'total' in order['discount']:
                            order_dict['discount'] = order['discount']['total']
                        elif 'discount' in order and 'amount' in order['discount']:
                            order_dict['discount'] = order['discount']['amount']
                        else:
                            order_dict['discount'] = 0
                        order_dict['service_tax'] = order['service_tax']['amount'] if 'service_tax' in order else 0
                        total_price = order_dict['sub_total_price'] - order_dict['discount'] + order_dict['service_tax']
                        order_dict['total_price'] = order['total_price'] if 'total_price' in order and order['total_price'] == total_price else total_price
                        order_dict['cash_collected'] = order['cash_collected'] if 'cash_collected' in order else 0
                        order_dict['cash_status'] = True if order_dict['cash_collected'] == int(math.ceil(order_dict['total_price'])) else False
                        if 'invoice_printed' in order:
                            order_dict['invoice_printed'] = order['invoice_printed']
                        elif order['status'] in [3, 4, 'delivery_progress', 'delivery_ready', 'clothes_delivered']:
                            order_dict['invoice_printed'] = 'true'
                        else:
                            order_dict['invoice_printed'] = 'false'
                    order_list.append(order_dict)
                except Exception as e:
                    print str(e)
                    print order, schedule_orders[order[order_type + '_id']]
                    return {'status': 'failure', 'error': e}, 403
            users = db.users.find(
                {
                    'user_id': {'$in': user_ids}
                }, {'user_id': 1, 'name': 1}
            )
            try:
                user_dict = {user['user_id']: user['name'] for user in users}
            except Exception as e:
                return {'status': 'failure', 'error': 'User db error'}, 403
            for order in order_list:
                order['name'] = user_dict[order['name']].encode('ascii', 'ignore').decode('ascii')
            try:
                return jsonify({'data': order_list})
            except Exception as e:
                print str(e)
        except Exception, e:
            return {'error': e, 'status': 'failure'}, 403


class MarketingReport(Resource):

    def periodic_report(self, start_datetime, end_datetime):
        try:
            orders = db.orders.find({
                'created_date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime,
                }
            })
            order_list = []
            address_ids = []
            user_ids = []
            pickup_ids = []
            for order in orders:
                order_dict = {}
                pickup_ids.append(order['pickup_id'])
                order['pickup_id'] = str(order['pickup_id'])
                order_dict['schedule_time'] = order['pickup_id']
                order_dict['created_date'] = order['created_date']
                order_dict['type'] = order['type']
                order_dict['status'] = order['status']
                order_dict['user_id'] = order['user_id']
                order_dict['hub'] = order['address_id']
                order_dict['sub_total_price'] = order['sub_total_price'] if 'sub_total_price' in order else 0
                if 'discount' in order and 'total' in order['discount']:
                    order_dict['discount'] = order['discount']['total']
                elif 'discount' in order and 'amount' in order['discount']:
                    order_dict['discount'] = order['discount']['amount']
                else:
                    order_dict['discount'] = 0
                order_dict['service_tax'] = order['service_tax']['amount'] if 'service_tax' in order else 0
                order_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
                user_ids.append(order['user_id'])
                address_ids.append(ObjectId(order['address_id']))
                order_list.append(order_dict)
        except Exception, e:
            return {'status': 'failure', 'error': e}
        schedules = db.schedules.find({
            '_id': {'$in': pickup_ids},
            'is_active': True,
            'is_pickup': True
        })
        schedule_items = {}
        for schedule in schedules:
            schedule['_id'] = str(schedule['_id'])
            schedule['schedule_date'] = schedule['schedule_date'].replace('/', '-')
            schedule_items[schedule['_id']] = schedule
        addresses = db.addresses.find({
            '_id': {'$in': address_ids}
        }, {'assigned_hub': 1})
        address_dict = {}
        for address in addresses:
            address['_id'] = str(address['_id'])
            address_dict[address['_id']] = address['assigned_hub'] if 'assigned_hub' in address else 0
        user_dict = {user['user_id']: user for user in db.users.find({'user_id': {'$in': user_ids}})}
        data_dict = {}
        date_buffer = start_datetime.date()
        while date_buffer <= end_datetime.date():
            data = {
                str(date_buffer): {
                    'laundry': 0,
                    'dryclean': 0,
                    'iron': 0,
                    'g_users': 0,
                    'fb_users': 0,
                    'unknown_users': 0,
                    '1st half': 0,
                    '2nd half': 0,
                    'new_users': 0,
                    'any_hub': 0,
                    'mrt_hub': 0,
                    'unknown_hub': 0,
                    'order_placed': 0,
                    'order_cancelled': 0,
                    'total_orders': 0,
                    'discount': 0,
                    'service_tax': 0,
                    'sub_total_price': 0,
                    'total_price': 0
                }
            }
            date_buffer = date_buffer + datetime.timedelta(days=1)
            data_dict.update(data)
        data_dict = OrderedDict(sorted(data_dict.items()))
        for order in order_list:
            try:
                date = order['created_date'].date()
                data_dict[str(date)]['total_orders'] += 1
                if schedule_items[order['schedule_time']]['schedule_time'] in ['8am - 10am', '10am - 12pm', '12pm - 2pm', '2pm - 4pm']:
                    data_dict[str(date)]['1st half'] += 1
                elif schedule_items[order['schedule_time']]['schedule_time'] in ['4pm - 6pm', '6pm - 8pm', '8pm - 10pm']:
                    data_dict[str(date)]['2nd half'] += 1
                data_dict[str(date)]['discount'] += order['discount']
                data_dict[str(date)]['service_tax'] += order['service_tax']
                data_dict[str(date)]['sub_total_price'] += order['sub_total_price']
                data_dict[str(date)]['total_price'] += order['total_price']
                if user_dict[order['user_id']]['createdAt'].day == date.day:
                    data_dict[str(date)]['new_users'] += 1
                if 'laundry' in order['type'] or 'WASH & IRON' in order['type']:
                    data_dict[str(date)]['laundry'] += 1
                if 'iron' in order['type'] or 'IRON' in order['type']:
                    data_dict[str(date)]['iron'] += 1
                if 'dryclean' in order['type'] or 'DRY_CLEANING' in order['type']:
                    data_dict[str(date)]['dryclean'] += 1

                if order['status'] not in [5, 6, 'order_cancelled', 'order_rejected']:
                    data_dict[str(date)]['order_placed'] += 1
                else:
                    data_dict[str(date)]['order_cancelled'] += 1

                if 'g_' in order['user_id']:
                    data_dict[str(date)]['g_users'] += 1
                elif 'fb_' in order['user_id']:
                    data_dict[str(date)]['fb_users'] += 1
                else:
                    data_dict[str(date)]['unknown_users'] += 1

                if address_dict[order['hub']] == 1:
                    data_dict[str(date)]['any_hub'] += 1
                elif address_dict[order['hub']] == 2:
                    data_dict[str(date)]['mrt_hub'] += 1
                else:
                    data_dict[str(date)]['unknown_hub'] += 1
            except Exception as e:
                print "error", str(e), order
                return {'status': 'faliure', 'error': str(e)}
        return jsonify({'data': data_dict})

    def daily_report(self, start_datetime, end_datetime):
        try:
            orders = db.orders.find({
                'created_date': {
                    '$gte': start_datetime,
                    '$lt': end_datetime
                },
                'status': {'$nin': [5, 'order_cancelled', 6, 'order_rejected']}
            })
            order_list = []
            user_ids = []
            user_dict = {}
            address_ids = []
            schedule_ids = []
            for order in orders:
                order_dict = {}
                user_ids.append(order['user_id'])
                user_dict[order['user_id']] = {
                    'order_dates': [],
                    'name': None,
                    'email': None,
                    'last_order_date': None,
                    'order_count': 0,
                    'signup_date': None,
                    'first_order_date': None
                }
                order_dict['order_id'] = order['order_id'] if 'order_id' in order and order['order_id'] else str(order['_id'])
                order_dict['name'] = order['user_id']
                order_dict['email'] = order['user_id']
                order_dict['pickup_date'] = str(order['pickup_id'])
                order_dict['delivery_date'] = str(order['delivery_id'])
                schedule_ids.extend([order['pickup_id'], order['delivery_id']])
                order_dict['phone'] = order['phone']
                address_ids.append(ObjectId(order['address_id']))
                order_dict['pincode'] = order['address_id']
                order_dict['hub'] = order['address_id']
                order_dict['type'] = ','.join(order['type']) if type(order['type']) == list else order['type']
                order_dict['service_type'] = 'express' if 'service_type' in order and order['service_type'] == 'express' else 'regular'
                order_dict['signup_date'] = order['user_id']
                order_dict['order_creation'] = str(order['created_date'])
                order_dict['order_count'] = order['user_id']
                order_dict['first_order_date'] = order['user_id']
                order_dict['last_order_date'] = order['user_id']
                order_items = ' '
                if 'order_items' in order:
                    for item in order['order_items']:
                        if 'quantity' in item:
                            order_items = order_items + item['title'] + ','
                order_dict['order_items'] = order_items.lstrip().rstrip()
                order_dict['sub_total_price'] = order['sub_total_price'] if 'sub_total_price' in order else 0
                if 'discount' in order and 'total' in order['discount']:
                    order_dict['discount'] = order['discount']['total']
                elif 'discount' in order and 'amount' in order['discount']:
                    order_dict['discount'] = order['discount']['amount']
                else:
                    order_dict['discount'] = 0
                order_dict['service_tax'] = order['service_tax']['amount'] if 'service_tax' in order else 0
                total_price = order_dict['sub_total_price'] - order_dict['discount'] + order_dict['service_tax']
                order_dict['total_price'] = order['total_price'] if 'total_price' in order and order['total_price'] == total_price else total_price
                order_list.append(order_dict)
            addresses = db.addresses.find({'_id': {'$in': address_ids}})
            address_dict = {}
            for address in addresses:
                try:
                    address['_id'] = str(address['_id'])
                    if 'pincode' not in address or address['pincode'] is None:
                        address['pincode'] = 0
                        if 'locality' in address and 'map_string' in address['locality']:
                            locality = address['locality']['map_string'].replace('\n', ' ').replace(',', '')
                            locality = ' '.join(locality.split())
                            split_text = locality.split(' ')
                            if 'Karnataka' in split_text and split_text.index('Karnataka') + 1 != len(split_text) and split_text[split_text.index('Karnataka') + 1].isdigit():
                                address['pincode'] = split_text[split_text.index('Karnataka') + 1]
                            else:
                                address_details = ' '
                                if address['address_1'] is not None:
                                    address_details += address['address_1'] + ' '
                                if address['address_2'] is not None:
                                    address_details += address['address_2']
                                address_details = address_details.replace('\n', ' ').replace(',', '')
                                text = ' '.join(address_details.split())
                                split_text = text.split(' ')
                                for t in split_text:
                                    if len(t) == 6 and t.isdigit():
                                        address['pincode'] = t
                                        break
                                if address['pincode'] is 0:
                                    address['pincode'] = split_text[split_text.index('Bengaluru') - 1] if 'Bengaluru' in split_text else locality
                        else:
                            address['pincode'] = 0
                            address_details = ' '
                            if address['address_1'] is not None:
                                address_details += address['address_1'] + ' '
                            if address['address_2'] is not None:
                                address_details += address['address_2']
                            locality = address_details.replace('\n', ' ').replace(',', '')
                            text = ' '.join(locality.split())
                            split_text = text.split(' ')
                            for t in split_text:
                                if len(t) == 6 and t.isdigit():
                                    address['pincode'] = t
                                    break
                            if address['pincode'] is 0:
                                address['pincode'] = text
                            # reverse = [float(address['locality']['lat']), float(address['locality']['lng'])]
                            # g = geocoder.google(reverse, method="reverse")
                            # address['pincode'] = g.json['postal'] if 'postal' in g.json else 'None'
                    address_dict[address['_id']] = {
                        'hub': 'MRT' if 'assigned_hub' in address and address['assigned_hub'] == 2 else 'ANY',
                        'pincode': address['pincode']
                    }
                except Exception as e:
                    print "address error", address
                    return {'error': e, 'stataus': 'failure'}, 403
            users = db.users.find({'user_id': {'$in': user_ids}})
            schedules = db.schedules.find({'_id': {'$in': schedule_ids}})
            schedule_dict = {}
            for schedule in schedules:
                schedule['_id'] = str(schedule['_id'])
                schedule_dict[schedule['_id']] = schedule
            aggregate_result = db.orders.aggregate([
                {'$sort': {
                    'created_date': -1}},
                {'$match': {
                    'user_id': {'$in': user_ids},
                    'status': {'$nin': [5, 'order_cancelled', 6, 'order_rejected']}
                }},
                {'$group': {
                    '_id': {
                        'created_date': '$created_date',
                        'user_id': '$user_id'
                    },
                    'count': {'$sum': 1}
                }}
            ])['result']
            for res in aggregate_result:
                user_dict[res['_id']['user_id']]['order_dates'].append(res['_id']['created_date'])
            for user in users:
                user_dict[user['user_id']]['name'] = user['name'] if 'name' in user and user['name'] else 'None'
                user_dict[user['user_id']]['email'] = user['email'] if 'email' in user and user['email'] else 'None'
                user_dict[user['user_id']]['order_dates'].sort()
                user_dict[user['user_id']]['signup_date'] = str(user['createdAt'])
                user_dict[user['user_id']]['order_count'] = len(user_dict[user['user_id']]['order_dates'])
                user_dict[user['user_id']]['last_order_date'] = user_dict[user['user_id']]['order_dates'][user_dict[user['user_id']]['order_count'] - 1]
                user_dict[user['user_id']]['first_order_date'] = user_dict[user['user_id']]['order_dates'][0]
            for order in order_list:
                try:
                    order['name'] = user_dict[order['name']]['name'].encode('ascii', 'ignore').decode('ascii')
                    order['email'] = user_dict[order['email']]['email'].encode('ascii', 'ignore').decode('ascii')
                    order['signup_date'] = user_dict[order['signup_date']]['signup_date']
                    order['order_count'] = user_dict[order['order_count']]['order_count']
                    order['last_order_date'] = user_dict[order['last_order_date']]['last_order_date']
                    order['first_order_date'] = user_dict[order['first_order_date']]['first_order_date']
                    order['pickup_date'] = schedule_dict[order['pickup_date']]['schedule_date']
                    order['delivery_date'] = schedule_dict[order['delivery_date']]['schedule_date']
                    order['pincode'] = address_dict[order['pincode']]['pincode'].encode('ascii', 'ignore').decode('ascii')
                    order['hub'] = address_dict[order['hub']]['hub'].encode('ascii', 'ignore').decode('ascii')
                except Exception as e:
                    print e, order
            return jsonify({'data': order_list})
        except Exception as e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 403

    def get(self, report_type, start_date=None, end_date=None):
        if report_type is 'periodic' and (start_date is None or end_date is None):
            return {'status': 'failure', 'error': 'Type is periodic.'}

        # utc_datetime = datetime.datetime.strptime(
        #     utils.get_current_time(), '%Y-%m-%d %H:%M:%S'
        # ) - datetime.timedelta(days=1)
        if start_date is not None:
            start_datetime = datetime.datetime.strptime(
                start_date + ' 00:00:00', '%Y-%m-%d %H:%M:%S'
            )
        if end_date is not None:
            end_datetime = datetime.datetime.strptime(
                end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'
            )
        if report_type == 'periodic':
            return self.periodic_report(start_datetime, end_datetime)
        elif report_type == 'daily':
            return self.daily_report(start_datetime, end_datetime)
        # elif report_type == 'justdial':
        #     week_start_date = utc_datetime - datetime.timedelta(days=6)
        #     return self.justdial_report(week_start_date.date(), utc_datetime.date())
        else:
            return {
                'status': 'failure',
                'error': 'Report type not provided/ invalid report type'
            }
