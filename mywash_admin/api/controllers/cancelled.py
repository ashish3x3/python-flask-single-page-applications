from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
import re

DELIVERY_TYPES = [
    'order',
    'missed',
    'rescheduled'
]

db = app.config['MONGO_CLIENT']['dealsup']

SEARCH_OPTIONS = ['email', 'name', 'phone', 'order_id']


class Cancelled(Resource):
    '''
    Given the date a list of deliverys are provided.
    '''
    def get(self, skip=None, limit=None):
        order_items = []
        user_ids = []

        aggregate_query = [
            {'$project': {'order_id': 1, 'user_id': 1, 'total_price': 1, 
                'delivery_id': 1, 'status': 1, 'order_items': 1, 'created_date': 1}},
            {
                '$match': {
                    'status': {
                        '$in': [5, 6, 'order_cancelled', 'order_rejected']
                    }
                }
            },
            {'$sort': {'created_date': -1}}
        ]
            
        if skip:
            aggregate_query.append({'$skip': skip})

        if limit:
            aggregate_query.append({'$limit': limit})
        
        data = db.orders.aggregate(aggregate_query)

        for order in data['result']:
            item_dict = {}
            item_dict['status'] = order['status']
            item_dict['order_id'] = str(order['_id'])
            item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
            item_dict['user_id'] = order['user_id']
            item_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
            order_items.append(item_dict)
            user_ids.append(order['user_id'])

        retrieved_users = {}
        for user in db.users.find(
            {'user_id': {'$in': user_ids}},
            {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1, 'phone': 1}
        ):
            user['_id'] = str(user['_id'])
            retrieved_users[user['user_id']] = user

        for item in order_items:
            item['user_info'] = retrieved_users[item['user_id']]

        return jsonify({'data': order_items})
