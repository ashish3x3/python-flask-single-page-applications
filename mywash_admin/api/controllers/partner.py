import copy
import datetime

from bson.objectid import ObjectId
from werkzeug.security import check_password_hash

from flask.ext.restful import Resource
from flask import request

from api.models import Partner as PartnerModel
from mywash_admin import app, db as pgdb
from api.controllers.address import Address

db = app.config['MONGO_CLIENT']['dealsup']
redis_client = app.config['REDIS_CLIENT']


class Partner(Resource):
    def get(self):
        args = copy.deepcopy(request.args)
        partner = None
        email = args['email']
        password = args['password']
        try:
            partner = PartnerModel.query.filter(
                (PartnerModel.email == email) &
                (PartnerModel.is_active == True)
            ).first()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error'}, 500
        if not partner:
            return {'status': 'failure', 'error': 'Invalid email'}, 403
        if not check_password_hash(partner.salt, password):
            return {'status': 'failure', 'error': 'Invalid Credentials'}, 403
        result = {
            'name': partner.data['name'],
            'phone': partner.data['phone'],
            'email': partner.email,
            'partner_id': partner.str_id,
            'tag': partner.tag,
            'is_sms_block': partner.is_sms_block
        }
        print result
        return {'status': 'success', 'result': result}

    def post(self):
        try:
            form = copy.deepcopy(request.form)
            print form
            try:
                partner = PartnerModel.query.filter(PartnerModel.email == form.get('email')).first()
                if partner:
                    return {'status': 'failure', 'error': 'Email already exists'}, 403
                partner = PartnerModel.query.filter(PartnerModel.tag == form.get('tag')).first()
                if partner:
                    return {'status': 'failure', 'error': 'Tag already exists'}, 403
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
            data = {
                'name': form.get('name').strip(),
                'phone': form.get('phone')
            }
            partner = PartnerModel(data=data, salt=form.get('password'))
            partner.email = form.get('email')
            partner.tag = form.get('tag')
            try:
                pgdb.session.add(partner)
                pgdb.session.commit()
                return {'status': 'success'}, 200
            except Exception as e:
                print e
                return {'status': 'failure', 'error': 'db insertion error'}
        except Exception as e:
            return {'status': 'success', 'error': str(e)}, 403


class PartnerUser(Resource):
    def get(self, partner_id, user_id=None):
        result = {}
        if user_id is None:
            try:
                users = db.users.find({'partner.id': partner_id}).sort('createdAt', -1)
                print "in try users....", users.count()
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
            result = []
            if users.count():
                for user in users:
                    result.append({
                        'name': user['name'],
                        'phone': user['phone'],
                        'email': user['email'],
                        'user_id': user['user_id'],
                        'partner_id': user['partner']['id']
                    })
        else:
            try:
                user = db.users.find_one({
                    'partner.id': partner_id,
                    'user_id': user_id
                })
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
            if user:
                result = {
                    'name': user['name'],
                    'phone': user['phone'],
                    'email': user['email'],
                    'user_id': user['user_id'],
                    'partner_id': user['partner']['id']
                }
        print "result....", result
        return {'status': 'success', 'result': result}, 200

    def post(self, partner_id):
        try:
            form = (request.form)
            if 'name' not in form or 'phone' not in form or 'email' not in form:
                return {'status': 'failure', 'error': 'Credentials not provided'}
            try:
                partner = PartnerModel.query.filter(
                    (PartnerModel.str_id == partner_id) &
                    (PartnerModel.is_active == True)
                ).first()
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
            user = db.users.find_one(
                {
                    'partner.id': partner_id,
                    '$or': [
                        {'email': form.get('email', '')},
                        {'phone': form.get('phone', '')}
                    ]
                }

            )
            print user
            if not user:
                schema = {
                    'name': form.get('name'),
                    'email': form.get('email'),
                    'phone': form.get('phone'),
                    'pictureUrl': form.get('pictureUrl', None),
                    'createdAt': datetime.datetime.utcnow(),
                    'updatedAt': datetime.datetime.utcnow(),
                    'user_id': partner.tag + '_' + str(ObjectId()),
                    'partner': {
                        'id': partner_id,
                        'name': partner.data['name']
                    },
                    'pictureUrl': ''
                }
            else:
                return {"status": 'failure', 'error': 'user already exists'}, 403
            try:
                db.users.insert(schema)
                result = {
                    'name': schema['name'],
                    'email': schema['email'],
                    'phone': schema['phone'],
                    'user_id': schema['user_id'],
                    'partner_id': schema['partner']['id']
                }
                print result
                return {"status": 'success', 'result': result}, 200
            except Exception, e:
                return {"status": 'failure', 'error': 'db error.'}, 500
        except Exception, e:
            return {'status': 'failure', 'error': str(e)}, 500

    def put(self, partner_id, user_id):
        try:
            form = (request.form)
            if 'name' not in form or 'phone' not in form or 'email' not in form:
                return {'status': 'failure', 'error': 'Credentials not provided'}
            data = {}
            if 'name' in form:
                data['name'] = form.get('name')
            if 'phone' in form:
                data['phone'] = form.get('phone')
            if 'email' in form:
                data['email'] = form.get('email')
            try:
                user = db.users.update({
                    'user_id': user_id,
                    'partner.id': partner_id,
                }, {'$set': data})
                print user
                return {"status": 'success'}, 200
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
        except Exception, e:
            return {'status': 'failure', 'error': str(e)}, 500


class PartnerOrderHistory(Resource):
    def get(self, partner_id, order_id=None):
        if order_id:
            try:
                order = db.orders.find_one({'_id': ObjectId(order_id)})
                user = db.users.find({
                    'user_id': order['user_id'],
                    'partner.id': partner_id
                })
                schedules = db.schedules.find({'_id': {'$in': [order['pickup_id'], order['delivery_id']]}})
                schedule_dict = {schedule['_id']: schedule for schedule in schedules}
                result = {
                    'name': user.get('name', ''),
                    'phone': user.get('phone', ''),
                    'user_id': user.get('user_id', ''),
                    'email': user.get('email', ''),
                    'order_id': order.get('order_id', ''),
                    'id': order.get('id', ''),
                    'order_id': order.get('order_id', ''),
                    'status': order.get('status', ''),
                    'type': ' '.join(order.get('type', [])),
                    'service_type': order.get('service_type', ''),
                    'pickup_date': schedule_dict[order['pickup_id']]['schedule_date'],
                    'pickup_time': schedule_dict[order['pickup_id']]['schedule_time'],
                    'delivery_date': schedule_dict[order['delivery_id']]['schedule_date'],
                    'delivery_time': schedule_dict[order['delivery_id']]['schedule_time'],
                    'partner_id': partner_id,
                    'user_id': order.get('user_id', '')
                }
                return {'status': 'success', 'result': result}, 200
            except Exception as e:
                return {'status': 'failure', 'error': 'order history db error: ' + str(e)}

        try:
            users = db.users.find({'partner.id': partner_id})
            user_dict = {}
            user_ids = []
            for user in users:
                user_dict[user.get('user_id', '')] = {
                    'name': user.get('name', ''),
                    'phone': user.get('phone', ''),
                    'email': user.get('email', '')
                }
                user_ids.append(user.get('user_id', ''))
        except Exception as e:
            return {'status': 'failure', 'error': 'user db error: ' + str(e)}
        try:
            orders = db.orders.find({'user_id': {'$in': user_ids}}).sort('created_date', -1)
            schedule_ids = []
            order_list = []
            for order in orders:
                schedule_ids.append(order['pickup_id'])
                schedule_ids.append(order['delivery_id'])
                order_list.append({
                    'order_id': order['order_id'],
                    'pickup_date': order['pickup_id'],
                    'pickup_time': order['pickup_id'],
                    'delivery_date': order['delivery_id'],
                    'delivery_time': order['delivery_id'],
                    'name': user_dict[order['user_id']].get('name', ''),
                    'email': user_dict[order['user_id']].get('email', ''),
                    'phone': order['phone'],
                    'id': str(order['_id']),
                    'status': order.get('status', ''),
                    'type': ' '.join(order.get('type', [])),
                    'service_type': order.get('service_type', ''),
                    'partner_id': partner_id,
                    'user_id': order.get('user_id', '')
                })
        except Exception as e:
            return {'status': 'failure', 'error': 'order db error: ' + str(e)}
        try:
            schedules = db.schedules.find({'_id': {'$in': schedule_ids}})
            schedule_dict = {schedule['_id']: schedule for schedule in schedules}
            for order in order_list:
                order['pickup_date'] = schedule_dict[order['pickup_date']]['schedule_date']
                order['pickup_time'] = schedule_dict[order['pickup_time']]['schedule_time']
                order['delivery_date'] = schedule_dict[order['delivery_date']]['schedule_date']
                order['delivery_time'] = schedule_dict[order['delivery_time']]['schedule_time']
        except Exception as e:
            return {'status': 'failure', 'error': 'schedule db error: ' + str(e)}
        return {'status': 'success', 'result': order_list}, 200


class PartnerUserSearch(Resource):
    def get(self, partner_id=None):
        form = copy.deepcopy(request.form)
        if 'phone' in form:
            try:
                users = db.users.find({
                    'partner.id': partner_id, 'phone': str(form['phone'])
                })
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
        elif 'email' in form:
            try:
                users = db.users.find({
                    'partner.id': partner_id, 'email': str(form['email'])
                })
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500
        else:
            return {'status': 'failure', 'error': 'Invalid entry for search'}, 403
        result = []
        for user in users:
            user_details = {}
            user_details['name'] = user.get('name')
            user_details['email'] = user.get('email')
            user_details['phone'] = user.get('phone')
            user_details['user_id'] = user.get('user_id')
            user_details['partner_id'] = user.get('partner_id')
            result.append(user_details)

        return {'status': 'success', 'result': result}, 200
