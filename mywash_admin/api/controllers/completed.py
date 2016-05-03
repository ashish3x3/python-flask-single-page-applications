from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
import re
from api.models import MywashHub

db = app.config['MONGO_CLIENT']['dealsup']

SEARCH_OPTIONS = ['email', 'name', 'phone', 'order_id']

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


class Completed(Resource):
    '''
    Given the date a list of deliverys are provided.
    '''
    def get(self, date):
        delivery_ids = []
        
        try:
            current_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y/%m/%d")
        except Exception, e:
            return {'status': 'failure', 'error': 'Format of date must be "yyyy-mm-dd"'}, 403

        try:
            deliveries = db.schedules.find(
                {'schedule_date': current_date, 'is_pickup': False, 'is_active': True},
                {'user_id': 0, 'created_date': 0}
            )
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500

        for item in deliveries:
            delivery_ids.append(item['_id'])

        # Rewind the pickup cursor
        deliveries.rewind()

        order_items = []
        user_ids = []

        try:
            orders = db.orders.find(
                {'delivery_id': {'$in': delivery_ids}, 'status': 'clothes_delivered'},
                {'order_id': 1, 'user_id': 1, 'total_price': 1, 
                'delivery_id': 1, 'status': 1, 'order_items': 1,
                'created_date': 1, 'pickup_id': 1, 'racks': 1, 'address_id': 1,'cash_collected': 1}
            ).sort('created_date', -1)
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500

        address_ids = []
        schedule_ids = []
        for order in orders:
            item_dict = {}
            item_dict['status'] = app.config['DEPRECATED_STATUS_MAP'][order['status']] if order['status'] in app.config['DEPRECATED_STATUS_MAP'] else order['status']
            item_dict['order_id'] = str(order['_id'])
            item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
            item_dict['user_id'] = order['user_id']
            item_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
            item_dict['created_date'] = order['created_date']
            item_dict['pickup_id'] = str(order['pickup_id'])
            item_dict['address_id'] = order['address_id']
            item_dict['delivery_id'] = str(order['delivery_id'])
            item_dict['racks'] = order['racks'] if 'racks' in order else []
            item_dict['cash_collected'] = order.get('cash_collected', 0)
            if item_dict['cash_collected'] == item_dict['total_price']:
                item_dict['paid'] = 'paid'
            elif item_dict['cash_collected'] >= item_dict['total_price']:
                item_dict['paid'] = 'excess_paid'
            else:
                item_dict['paid'] = 'other'

            order_items.append(item_dict)
            user_ids.append(order['user_id'])
            schedule_ids.append(order['delivery_id'])
            schedule_ids.append(order['pickup_id'])
            try:
                address_ids.append(bson.ObjectId(order['address_id']))
            except Exception, e:
                pass

        try:
            schedules = db.schedules.find(
                {'_id': {'$in': schedule_ids}},
                {'user_id': 0, 'created_date': 0}
            )
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500

        schedule_data = {}
        for schedule in schedules:
            schedule['updated-date'] = str(schedule['updated-date'])
            schedule['_id'] = str(schedule['_id'])
            schedule_data[schedule['_id']] = schedule

        retrieved_users = {}
        for user in db.users.find(
            {'user_id': {'$in': user_ids}},
            {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1, 'phone': 1}
        ):
            user['_id'] = str(user['_id'])
            retrieved_users[user['user_id']] = user

        address_dict = {}
        for address in db.addresses.find({'_id': {'$in': address_ids}}):
            address_dict[str(address['_id'])] = address['assigned_hub'] if 'assigned_hub' in address else None

        for item in order_items:
            item['user_info'] = retrieved_users[item['user_id']] if item['user_id'] in retrieved_users else {}
            item['pickup_data'] = schedule_data[item['pickup_id']]
            item['delivery_data'] = schedule_data[item['delivery_id']]

            if item['address_id'] in address_dict and address_dict[item['address_id']] is not None:
                item['hub'] = HUBS[address_dict[item['address_id']]]
            else:
                item['hub'] = HUBS[1]

        return jsonify({'data': order_items})
