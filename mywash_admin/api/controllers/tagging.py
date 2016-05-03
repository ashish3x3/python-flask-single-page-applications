from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
import re
import json
from api.models import TagBundle
from api.models import MywashHub

PICKUP_TYPES = [
    'order',
    'missed',
    'rescheduled'
]

db = app.config['MONGO_CLIENT']['dealsup']

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


class TaggingDate(Resource):
    '''
    Given the date a list of tags are provided.
    '''
    def get(self, tagging_type=None, date=None, time=None):
        if tagging_type and tagging_type not in PICKUP_TYPES:
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
        
        tagging_ids = []
        tagging_items = {}

        if current_date:
            tags = db.schedules.find({'schedule_date': current_date, 'is_pickup': True, 'is_active': True})
        else:
            tags = db.schedules.find({'is_pickup': True, 'is_active': True})

        for item in tags:
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
                if tagging_type == 'order':
                    if current_time < schedule_time_ceil:
                        continue
                elif tagging_type == 'missed':
                    if current_time >= schedule_time_ceil:
                        continue

            tagging_ids.append(item['_id'])
            item['schedule_time_ceil'] = int(schedule_time_floor.strftime("%H")) + int(schedule_time_ceil.strftime("%H"))
            tagging_items[str(item['_id'])] = item

        order_items = []
        user_ids = []
        try:
            orders = db.orders.find({
                'pickup_id': {'$in': tagging_ids}, 
                    'status': {
                        '$in': ['pickup_complete']
                    }
                }, {'order_id': 1, 'user_id': 1, 'total_price': 1, 'pickup_id': 1, 
                'status': 1, 'order_items': 1, 'is_paid': 1, 'bag': 1,'service_type':1, 'address_id': 1}
            )
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        address_ids = []
        for order in orders:
            item_dict = {}
            item_dict['status'] = order['status']
            item_dict['order_id'] = str(order['_id'])
            item_dict['is_paid'] = order['is_paid'] if 'is_paid' in order else False
            item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
            item_dict['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
            item_dict['user_id'] = order['user_id']
            item_dict['bag'] = order['bag'] if 'bag' in order else {}
            item_dict['address_id'] = order.get('address_id', None)
            item_dict['total_quantity'] = 0
            if 'order_items' in order:
                for item in order['order_items']:
                    if 'quantity' in item and 'laundry' in item['quantity']:
                        item_dict['total_quantity'] += item['quantity']['laundry']
                    if 'quantity' in item and 'dryclean' in item['quantity']:
                        item_dict['total_quantity'] += item['quantity']['dryclean']
                    if 'quantity' in item and 'iron' in item['quantity']:
                        item_dict['total_quantity'] += item['quantity']['iron']

            item_dict['schedule_time'] = tagging_items[str(order['pickup_id'])]['schedule_time_ceil']
            item_dict['schedule_time_range'] = tagging_items[str(order['pickup_id'])]['schedule_time']
            order_items.append(item_dict)
            user_ids.append(order['user_id'])

            try:
                address_ids.append(bson.ObjectId(order['address_id']))
            except Exception, e:
                pass

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
        order = db.orders.find_one({'_id': bson.ObjectId(form['order_id'])})
        now = datetime.utcnow()
        if 'date' in form:
            db.schedules.update({
                '_id': order['pickup_id']
            }, {
                '$set': {
                    'schedule_date': form['date'],
                    'updated-time': now
                }
            })
        elif 'time' in form:
            db.schedules.update({
                '_id': order['pickup_id']
            }, {
                '$set': {
                    'schedule_time': form['time'],
                    'updated-time': now
                }
            })
        return {'status': 'success'}


class Tags(Resource):
    
    def get(self, order_ids):
        try:
            order_ids = json.loads(order_ids)
        except Exception, e:
            return {'status': 'failure', 'error': 'Invaid format.'}, 404
        
        if not isinstance(order_ids, list):
            return {'status': 'failure', 'error': 'Invaid format.'}, 404

        order_ids = [bson.ObjectId(order_id) for order_id in order_ids]

        orders = db.orders.aggregate([
            {'$project': {'order_items.quantity': 1, 'order_items.title': 1, 'user_id': 1, 'bag': 1, 'pickup_id': 1, 'delivery_id': 1, 'order_id': 1}},
            {'$match': {'_id': {'$in': order_ids}}}
        ])

        tags = []
        user_ids = []
        schedule_ids = []
        for order in orders['result']:
            tag = {}
            laundryCount = 0
            drycleanCount = 0
            ironCount = 0
            laundrySummary = []
            drycleanSummary = []
            ironSummary = []
            for item in order['order_items']:
                if not item or 'quantity' not in item:
                    continue
                if 'laundry' in item['quantity']:
                    laundryCount += item['quantity']['laundry']
                    laundrySummary.append({'title': item['title'], 'quantity': item['quantity']['laundry']})

                if 'dryclean' in item['quantity']:
                    drycleanCount += item['quantity']['dryclean']
                    drycleanSummary.append({'title': item['title'], 'quantity': item['quantity']['dryclean']})

                if 'iron' in item['quantity']:
                    ironCount += item['quantity']['iron']
                    ironSummary.append({'title': item['title'], 'quantity': item['quantity']['iron']})


            if 'bag' not in order:
                order['bag'] = {'laundry': "", 'dryclean': "", 'iron': ""}
            
            tag['laundry'] = {
                'bag': order['bag']['laundry'] if 'laundry' in order['bag'] else "",
                'quantity': laundryCount,
                'summary': laundrySummary
            }

            tag['dryclean'] = {
                'bag': order['bag']['dryclean'] if 'dryclean' in order['bag'] else "",
                'quantity': drycleanCount,
                'summary': drycleanSummary
            }

            tag['iron'] = {
                'bag': order['bag']['iron'] if 'iron' in order['bag'] else "",
                'quantity': ironCount,
                'summary': ironSummary
            }

            tag['user_id'] = order['user_id']
            tag['order_id'] = order['order_id']
            tag['pickup_id'] = str(order['pickup_id'])
            tag['delivery_id'] = str(order['delivery_id'])

            schedule_ids.append(order['pickup_id'])
            schedule_ids.append(order['delivery_id'])
            tags.append(tag)
            user_ids.append(order['user_id'])
            
        schedules = db.schedules.find({'_id': {'$in': schedule_ids}}, {'schedule_date': 1, 'schedule_time': 1})
        schedules_dict = {}
        for schedule in schedules:
            schedule['_id'] = str(schedule['_id'])
            schedules_dict[schedule['_id']] = schedule

        users = db.users.aggregate([
            {'$project': {'name': 1, 'phone': 1, 'user_id': 1}},
            {'$match': {'user_id': {'$in': user_ids}}}
        ])

        all_users = {}
        for user in users['result']:
            all_users[user['user_id']] = {'name': user['name']}

        for tag in tags:
            tag['name'] = all_users[tag['user_id']]['name']

            tag['pickup_date'] = schedules_dict[tag['pickup_id']]['schedule_date']
            tag['pickup_time'] = schedules_dict[tag['pickup_id']]['schedule_time']

            tag['delivery_date'] = schedules_dict[tag['delivery_id']]['schedule_date']
            tag['delivery_time'] = schedules_dict[tag['delivery_id']]['schedule_time']

        return jsonify({'data': tags})


class TagBags(Resource):

    def get(self, pickup_date, bag_name=None):
        if not re.match(r'\d{4}-\d{2}-\d{2}', pickup_date):
            return {'status': 'failure', 'error': 'Date format wrong.'}, 403
        else:
            bundle_date = datetime.strptime(pickup_date, "%Y-%m-%d")
            pickup_date = bundle_date.strftime("%Y/%m/%d")

        if not bag_name:
            return {'status': 'failure', 'error': 'No bag name provided.'}, 403

        try:
            pickups = db.schedules.find({'schedule_date': pickup_date})
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        pickup_ids = [pickup['_id'] for pickup in pickups]

        try:
            orders = db.orders.aggregate(
                {
                    '$match': {
                        'pickup_id': {'$in': pickup_ids},
                        'status': 'pickup_complete',
                        '$or': [
                            {'bag.laundry': re.compile("^" + bag_name, re.IGNORECASE)},
                            {'bag.dryclean': re.compile("^" + bag_name, re.IGNORECASE)},
                            {'bag.iron': re.compile("^" + bag_name, re.IGNORECASE)}
                        ]
                    }
                }
            )
            orders = orders['result']
        except Exception:
            return {'status': 'failure', 'error': 'db error.'}, 500

        order_ids = [order['user_id'] for order in orders]

        try:
            users = db.users.find({'user_id': {'$in': order_ids}})
        except Exception:
            return {'status': 'failure', 'error': 'db error.'}, 500

        try:
            used_bags_raw = TagBundle.query.filter(TagBundle.date == bundle_date)
            used_bags_set = set()
            for bag in used_bags_raw:
                used_bags_set.update(bag.bags)
            used_bags_set = list(used_bags_set)
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        user_names = {user['user_id']: user['name'] for user in users}

        result = []
        for order in orders:
            for bags in order['bag'].values():
                for bag in bags:
                    if bag.startswith(bag_name):
                        if bag in used_bags_set:
                            continue
                        item = {
                            'name': user_names[order['user_id']],
                            'bag': bag
                        }
                        result.append(item)

        return {'data': result}
        
