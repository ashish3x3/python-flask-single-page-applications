from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import bson
import copy
import re
import json
from mywash_admin.lib import utils
from mywash_admin.lib import emails
from random import randint
from mywash_admin.lib.loggers import MongoLogger

db = app.config['MONGO_CLIENT']['dealsup']

SEARCH_OPTIONS = ['email', 'name', 'phone']

LOGGER = MongoLogger('mywash_logs', 'missing_phone_logs')


class User(Resource):
    def _user_schema(self):
        return {
            'name': None,
            'email': None,
            'phone': None,
            'createdAt': datetime.utcnow(),
            'updated_date': datetime.utcnow(),
            'credits': 0,
            'updatedAt': datetime.utcnow(),
            'pictureUrl': None
        }

    def _schema(self):
        return {
            'user_data': None,
            'counts': {
                'placed': 0,
                'cancelled': 0,
                'completed': 0,
            }
        }

    def get(self, user_id=None, skip=None, limit=None):
        users = None
        if user_id:
            users = db.users.find_one(
                {'user_id': user_id},
                {'_id': 0, 'authData': 0, 'createdAt': 0, 'upadated_date': 0}
            )
            users = [users]
        else:
            skip = 0 if not skip else skip
            limit = 20 if not limit else limit
            users = db.users.find(
                {},
                {'_id': 0, 'authData': 0, 'createdAt': 0, 'upadated_date': 0}
            ).sort("_id", -1).skip(skip).limit(limit)

        users_dict = {}
        users = list(users)
        for user in users:
            users_dict[user['user_id']] = user

        orders = None
        try:
            orders = db.orders.find({'user_id': {'$in': users_dict.keys()}})
        except Exception:
            return jsonify({'status': "failure", 'error': "db error"})

        orders_dict = {}
        for order in orders:
            if 'user_id' not in order:
                continue

            if order['user_id'] not in orders_dict:
                orders_dict[order['user_id']] = self._schema()['counts']
            
            orders_dict[order['user_id']]['placed'] += 1

            if order['status'] == 4 or order['status'] == 'clothes_delivered':
                orders_dict[order['user_id']]['completed'] += 1

            if order['status'] == 5 or order['status'] == 6 or order['status'] == 'order_cancelled' or order['status'] == 'order_rejected':
                orders_dict[order['user_id']]['cancelled'] += 1

        result_list = []
        for user in users:
            item = self._schema()
            item['user_data'] = users_dict[user['user_id']]
            if user['user_id'] in orders_dict:
                item['counts'] = orders_dict[user['user_id']]
            result_list.append(item)

        total_count = 0
        try:
            total_count = db.users.count()
        except Exception:
            return jsonify({'status': "failure", 'error': "db error"})

        result = {
            'total_count': total_count,
            'users': result_list
        }

        return jsonify({'data': result})

    def post(self):
        form = copy.deepcopy(request.form)

        if not form['email']:
            return {'status': 'failure', 'error': 'no email provided.'}, 400

        if not utils.validateEmail(form['email']):
            return {'status': 'failure', 'error': 'invalid email.'}, 400

        if not form['phone']:
            return {'status': 'failure', 'error': 'no phone provided.'}, 400

        if not form['name']:
            return {'status': 'failure', 'error': 'no name provided.'}, 400

        schema = self._user_schema()
        schema['name'] = form['name']
        schema['email'] = form['email']
        schema['phone'] = form['phone']
        schema['createdAt'] = datetime.utcnow()
        print schema
        if 'user_id' not in form or not form['user_id']:
            schema['user_id'] = str(bson.ObjectId())
        try:
            user_id = db.users.insert(schema)
            return {"status": 'success', 'id': str(schema['user_id'])}
        except Exception, e:
            return {"status": 'failure', 'error': 'db error.'}, 500

    def put(self, user_id):
        form = copy.deepcopy(request.form)
        update_data = {}
        try:
            user = db.users.find_one({'user_id': user_id})
            if not user:
                return {'status': 'failure', 'error': 'user doesn\'t exist.'}, 403
        except Exception, e:
            return {"status": 'failure', 'error': 'db error.'}, 500

        if 'phone' in form:
            if not form['phone'].strip():
                global LOGGER
                LOGGER.error(
                    "missing phone number",
                    event='missing_phone_put_event',
                    user_id=user_id,
                    user_agent=request.headers.get('User-Agent', '')
                )
            update_data['phone'] = form['phone']
            update_data['authData.phone'] = form['phone']

        if 'name' in form:
            update_data['name'] = form['name']
            update_data['authData.name'] = form['name']

        if 'email' in form and form['email'].strip():
            if not utils.validateEmail(form['email']):
                return {'status': 'failure', 'error': 'invalid email.'}, 400
            update_data['email'] = form['email'].strip()
            update_data['authData.email'] = form['email'].strip()

        if 'credits' in form and form['credits'] is not None and form['credits']:
            credits = json.loads(form['credits'])
            try:
                increment = int(credits['add']) - int(credits['deduct'])
                total_credit = 0
                if 'credits' not in user:
                    total_credit = 0
                else:
                    total_credit = int(user['credits'])
                total_credit += increment

                if total_credit < 0:
                    total_credit = 0
                update_data['credits'] = total_credit
            except Exception, e:
                return {"status": 'failure', 'error': 'Invalid credits.'}, 403

        if len(update_data):
            update_data["updatedAt"] = datetime.now()
            try:
                db.users.update(
                    {'user_id': user_id},
                    {'$set': update_data}
                )
            except Exception, e:
                return {"status": 'failure', 'error': 'db error.'}, 500
            return {"status": 'success'}

        return {"status": 'failure', 'error': 'No parameter provided for update.'}, 403
            

class UserSearch(User):
    def get(self, term, skip=0, limit=20):
        if not term:
            return {"status": 'failure', 'error': 'no search term provided.'}, 400

        term_split = term.split(":")

        if term_split[0].lower() not in SEARCH_OPTIONS:
            return {"status": 'failure', 'error': '"%s" is not a valid search criteria.'}, 400

        if len(term_split) < 2:
            return {"status": 'failure', 'error': 'not enough search arguments.'}, 400

        search_arg = ":".join(term_split[1:])
        search_arg = search_arg.strip()

        if not search_arg:
            return {"status": 'failure', 'error': 'not enough search arguments.'}, 400

        match_pipe = {}
        if term_split[0] == 'email':
            match_pipe['email'] = re.compile(search_arg, re.IGNORECASE)
        elif term_split[0] == 'name':
            match_pipe['name'] = re.compile(search_arg, re.IGNORECASE)
        elif term_split[0] == 'phone':
            match_pipe['phone'] = re.compile(search_arg, re.IGNORECASE)

        aggregate_query = [
            {
                '$project': {
                    'name': 1, 'pictureUrl': 1, 'user_id': 1, 'email': 1,
                    'credits': 1, 'phone': 1, 'phone_is_valid': 1
                }
            },
            {'$match': match_pipe},
            {'$skip': skip},
            {'$limit': limit}
        ]
        users = db.users.aggregate(aggregate_query)

        users_dict = {}
        for user in users['result']:
            user['_id'] = str(user['_id'])
            users_dict[user['user_id']] = user

        try:
            orders = db.orders.find({'user_id': {'$in': users_dict.keys()}})
        except Exception:
            return jsonify({'status': "failure", 'error': "db error"})

        orders_dict = {}
        for order in orders:
            if 'user_id' not in order:
                continue

            if order['user_id'] not in orders_dict:
                orders_dict[order['user_id']] = self._schema()['counts']

            orders_dict[order['user_id']]['placed'] += 1

            if order['status'] == 4 or order['status'] == 'clothes_delivered':
                orders_dict[order['user_id']]['completed'] += 1

            if order['status'] == 5 or order['status'] == 6 or order['status'] == 'order_cancelled' or order['status'] == 'order_rejected':
                orders_dict[order['user_id']]['cancelled'] += 1

        result_list = []
        for user in users['result']:
            item = self._schema()
            item['user_data'] = users_dict[user['user_id']]
            if user['user_id'] in orders_dict:
                item['counts'] = orders_dict[user['user_id']]
            result_list.append(item)

        total_count = 0
        try:
            total_count = db.users.count()
        except Exception:
            return jsonify({'status': "failure", 'error': "db error"})

        result = {
            'total_count': total_count,
            'users': result_list
        }

        return jsonify({'data': result})


class UserPhoneVerification(Resource):
    def _validate_phone(self, phone):
        if not ((len(phone) == 10 or len(phone) == 12) and phone.isdigit()):
            return {'status': 'failure', 'error': 'Invalid phone number.'}, 403

        return {'status': 'success'}

    def _send_otp(self, phone, sms):
        status_info = False
        try:
            status_info = emails.mywash_order_transactional_sms(phone.strip(), sms)
        except Exception, e:
            pass
        return {'status': 'success'}

    def post(self):
        form = copy.deepcopy(request.form)
        phone = form['phone']
        user_id = form['user_id']
        data = self._validate_phone(phone)

        random_otp = 0
        status = data['status'] if 'status' in data else data[0]['status']
        if status is 'failure':
            return data
        if user_id:
            if len(phone) == 10:
                phone = phone
            random_otp = randint(10000, 99999)
            sms = "Hi, Greeting from MyWash! Your phone verification code is " + str(random_otp) + ". Thank you."
            sms_result = self._send_otp(phone, sms)

            if not phone.strip():
                global LOGGER
                LOGGER.error(
                    "missing phone number",
                    event='missing_phone_post_event',
                    user_id=user_id,
                    user_agent=request.headers.get('User-Agent', '')
                )
            db.users.update(
                {'user_id': user_id},
                {'$set': {'phone': phone, 'phone_is_valid': False}}
            )
        return jsonify({'otp': random_otp})
