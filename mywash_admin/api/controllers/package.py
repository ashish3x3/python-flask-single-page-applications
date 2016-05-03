from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
from api.models import MywashHub

DELIVERY_TYPES = [
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


class Packaging(Resource):
    '''
    Given the date a list of deliverys are provided.
    '''
    def get(self, **kwargs):
        order_items = []
        user_ids = []
        delivery_ids = []
        limit = 20
        skip = 0
        package_count = 0
        if 'limit' in kwargs:
            limit = kwargs['limit']

        if 'skip' in kwargs:
            skip = kwargs['skip']

        try:
            data = db.orders.find(
                {'status': "washing"},
                {'order_id': 1, 'user_id': 1, 'total_price': 1, 
                'delivery_id': 1, 'status': 1, 'order_items': 1, 'created_date': 1,
                'invoice_printed': 1, 'racks': 1,'service_type':1, 'address_id': 1}
            )
            package_count = data.count()
            data = data.sort('created_date', -1).skip(skip).limit(limit)
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "db error."}, 500

        address_ids = []

        for order in data:
            item_dict = {}
            item_dict['status'] = order['status']
            item_dict['invoice_printed'] = order['invoice_printed'] if 'invoice_printed' in order else False
            item_dict['order_id'] = str(order['_id'])
            item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
            item_dict['user_id'] = order['user_id']
            item_dict['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
            item_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
            item_dict['delivery_id'] = str(order['delivery_id'])
            item_dict['racks'] = order['racks'] if 'racks' in order else []
            item_dict['address_id'] = order.get('address_id', None)
            order_items.append(item_dict)
            user_ids.append(order['user_id'])
            delivery_ids.append(order['delivery_id'])

            try:
                address_ids.append(bson.ObjectId(order['address_id']))
            except Exception, e:
                pass

        deliveries = {}
        try:
            deliveries_data = db.schedules.find({'_id': {'$in': delivery_ids}}, {'created_date': 0, 'updated_date': 0})
        except Exception, e:
            return {'status': 'failure', 'error': "db error."}, 500

        for delivery in deliveries_data:
            delivery['_id'] = str(delivery['_id'])
            deliveries[str(delivery['_id'])] = delivery

        retrieved_users = {}
        for user in db.users.find(
            {'user_id': {'$in': user_ids}},
            {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1, 'phone': 1}
        ):
            user['_id'] = str(user['_id'])
            retrieved_users[user['user_id']] = user

        address_dict = {}
        for address in db.addresses.find({'_id': {'$in': address_ids}}):
            if 'assigned_hub' in address:
                address_dict[str(address['_id'])] = int(address['assigned_hub'])

        for item in order_items:
            item['delivery_data'] = deliveries[item['delivery_id']]
            item['user_info'] = retrieved_users[item['user_id']]
            if item['address_id'] in address_dict:
                item['hub'] = HUBS[address_dict[item['address_id']]]
            else:
                item['hub'] = HUBS[1]

        return jsonify({'data': order_items, 'item_count': package_count})

    def put(self):
        form = copy.deepcopy(request.form)
        order = db.orders.find_one({'_id': bson.ObjectId(form['order_id'])})
        now = datetime.utcnow()
        if 'date' in form:
            try:
                db.schedules.update({
                    '_id': order['delivery_id']
                }, {
                    '$set': {
                        'schedule_date': form['date'],
                        'updated-time': now
                    }
                })
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 404
            
        elif 'time' in form:
            try:
                db.schedules.update({
                    '_id': order['delivery_id']
                }, {
                    '$set': {
                        'schedule_time': form['time'],
                        'updated-time': now
                    }
                })
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 404

        return {'status': 'success'}

