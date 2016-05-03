from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime

from mywash_admin import app, db as pgdb
from mywash_admin.lib import emails
from api.models import MywashHub, Reason
from mywash_admin.lib.loggers import MongoLogger
import bson
import traceback
import copy
import re
import sys
import random
import json
from mywash_admin.lib import utils
from api.models import Employee as EmployeeModel
from api.controllers.coupon import Coupon
from api.models import UserOrderCoupon as UserOrderCouponModel
from api.models import Coupon as CouponModel
from api.models import OnlineTransaction, Partner
from mywash_admin import app, db as pgdb
import importlib
from requests_futures.sessions import FuturesSession


db = app.config['MONGO_CLIENT']['dealsup']
arequests = FuturesSession(max_workers=1)

SMS_LOGGER = MongoLogger('mywash_logs', 'sms_logs')

STATUSES = []
for i in db.statuses.find():
    STATUSES += [j['name_id'] for j in i['status']]

SEARCH_OPTIONS = ['email', 'name', 'phone', 'oid']

TIMESLOTS = app.config['TIMESLOTS']

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


class Order(Resource):
    char_collection = range(48, 58)
    char_collection2 = range(65, 91) + range(48, 58)
    hash_num = len(char_collection)

    def uniqueOrderId(self):
        datepart_list = datetime.utcnow().strftime("%y-%m-%d").split("-")
        datepart = chr(self.char_collection2[int(datepart_list[0])-1]) \
         + chr(self.char_collection2[int(datepart_list[1])-1]) \
         + chr(self.char_collection2[int(datepart_list[2])-1])
        shift = random.randint(0, 9)
        last_part = ""
        for i in range(0, 5):
            selection = random.randint(0, self.hash_num-1)
            index = (selection + shift) % self.hash_num
            last_part += chr(self.char_collection[index])
        order_id = datepart + last_part
        if db.orders.find({'order_id': order_id}).count():
            return self.uniqueOrderId()
        else:
            return order_id

    def base_schedule(self):
        return {
            "address_id": 0,
            "user_id": 0,
            "schedule_time": "",
            "schedule_date": "",
            "is_active": True,
            "is_pickup": True,
            "created_date": datetime.now(),
            "updated-date": datetime.now(),
            "is_completed": True,
        }

    def base_order(self):
        data = {
            "user_id": "",
            "address_id": "",
            "status": "order_placed",
            "rating": None,
            "special_instructions": "",
            "payment_id": "",
            "pickup_id": 0,
            "delivery_id": 0,
            "coupon": {},
            "order_price": 0,
            "final_price": 0,
            "credits_applied": 0,
            "order_items": {},#{"item_id": {quantity,constants.wash},
            "agent_verified_items": False,
            "phone": "",
            "last_credit_used":0,
            "type": "",
            "service_type":"",
            "cash_collected":0,
            "created_date": datetime.now(),
            "updated_date": datetime.now(),
            "order_id": self.uniqueOrderId()
        }
        return data

    def _get_date_wise(self, date, order_type):
        pickup_ids = []
        
        is_pickup = True if order_type == 'pickup' else False
        
        try:
            current_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y/%m/%d")
        except Exception, e:
            return {'error': 'Format of date must be "yyyy-mm-dd"'}, 404

        try:
            pickups = db.schedules.find(
                {'schedule_date': current_date, 'is_pickup': is_pickup, 'is_active': True},
                {'user_id': 0, 'created_date': 0}
            )
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500

        for item in pickups:
            pickup_ids.append(item['_id'])

        # Rewind the pickup cursor
        pickups.rewind()

        order_items = []
        user_ids = []

        try:
            orders = db.orders.find(
                {'pickup_id' if is_pickup else 'delivery_id': {'$in': pickup_ids}},
                {'order_id': 1, 'user_id': 1, 'total_price': 1, 
                'delivery_id': 1, 'status': 1, 'order_items': 1,
                'created_date': 1, 'pickup_id': 1, 'racks': 1, 'address_id': 1,'service_type':1,
                'cash_collected': 1}
            ).sort('created_date', -1)
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500

        address_ids = []
        schedule_ids = []
        for order in orders:
            if 'is_paid' in order:
                if isinstance(order['is_paid'], bool):
                    order['is_paid'] = 'paid' if order['is_paid'] else 'not_paid'

            item_dict = {}
            item_dict['is_paid'] =  order['is_paid'] if 'is_paid' in order else 'not_paid'
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
            item_dict['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
            item_dict['cash_collected'] = order.get('cash_collected', 0)

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

    def _coupon_verify(self, coupon_name, user_id, service_type):
        try:
            coupon_data = CouponModel.query.filter(
                CouponModel.data['name'].astext == coupon_name.strip().lower()
            ).first()
        except Exception, e:
            print e
            return {"status": 'failure', "error": "db error"}, 500

        # code for importing the class of coupon and verifying it
        if coupon_data and coupon_data.str_id:
            try:
                user_id = str(db.users.find_one({"user_id": user_id})["_id"])
                coupon_file = importlib.import_module("api.coupons.%s" % coupon_data.str_id)
                coupon = coupon_file.Coupon(coupon_data.str_id,service_type, user_id)
                verification_message = coupon.validate()
            except ImportError, e:
                # Display error messag
                print e
                return {"status": 'failure', "error": "Unexpected Error: Coupon Validity unknown"}, 403

            if verification_message['status'] == "success":
                try:
                    user_order_coupon = UserOrderCouponModel()
                    user_order_coupon.user = user_id
                    user_order_coupon.coupon = str(coupon_data.str_id)
                    pgdb.session.add(user_order_coupon)
                    pgdb.session.commit()

                    verification_message['uoc_id'] = user_order_coupon.str_id
                    verification_message['status'] = "success"

                except Exception, e:
                    return {'status': 'failure', 'error': 'db error'}, 500

            return verification_message

        return {'status': 'failure', 'error': 'Invalid coupon.'}, 403

    def get(self, **kwargs):
        order_id = None
        skip = 0
        limit = 20
        date = None
        order_type = None

        if 'order_id' in kwargs:
            order_id = kwargs['order_id']
        if 'skip' in kwargs:
            skip = int(kwargs['skip'])
        if 'limit' in kwargs:
            limit = int(kwargs['limit'])
        if 'date' in kwargs:
            date = kwargs['date']

        if 'order_type' in kwargs:
            order_type = kwargs['order_type']
            if order_type not in ['pickup', 'delivery']:
                return {'status': 'failure', 'error': "Invalid order type"}, 403
        # TO BE IMPLEMENTED, ObjectId's must be flattened
        if order_id:
            try:
                order = db.orders.find_one({'_id': bson.ObjectId(order_id)}, {'_id': 0, 'created_date': 0})
                schedules = db.schedules.find(
                    {'_id': {'$in': [order['delivery_id'], order['pickup_id']]}},
                    {'user_id': 0, '_id': 0, 'created_date': 0}
                )
                for schedule in schedules:
                    schedule['updated-date'] = str(schedule['updated-date'])
                    if schedule['is_pickup']:
                        order['pickup_data'] = schedule
                    else:
                        order['delivery_data'] = schedule

                address = db.addresses.find_one({'_id': bson.ObjectId(order['address_id'])})
                order['delivery_id'] = str(order['delivery_id'])
                order['pickup_id'] = str(order['pickup_id'])
                order['updated_date'] = str(order['updated_date'])

                if 'assigned_hub' in address:
                    order['hub'] = HUBS[address['assigned_hub']]
                else:
                    order['hub'] = HUBS[1]

                if 'racks' not in order:
                    order['racks'] = []
                return jsonify({"data": order})
            except Exception, e:
                return {'status': 'failure', 'error': "database error"}, 500

        elif date is not None:
            return self._get_date_wise(date, order_type)
        else:
            order_items = []
            user_ids = []

            try:
                orders = db.orders.find(
                    {},
                    {'order_id': 1, 'user_id': 1, 'total_price': 1, 
                    'delivery_id': 1, 'status': 1, 'order_items': 1,
                    'created_date': 1, 'pickup_id': 1, 'racks': 1, 'address_id': 1,'service_type':1,
                    'cash_collected': 1,'last_credit_used':1}
                ).sort('created_date', -1)
                if skip:
                    orders = orders.skip(skip)
                if limit:
                    orders = orders.limit(limit)
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error'}, 500

            address_ids = []
            schedule_ids = []
            for order in orders:
                if 'is_paid' in order:
                    if isinstance(order['is_paid'], bool):
                        order['is_paid'] = 'paid' if order['is_paid'] else 'not_paid'

                item_dict = {}

                item_dict['is_paid'] =  order['is_paid'] if 'is_paid' in order else 'not_paid'
                item_dict = {}
                item_dict['status'] = app.config['DEPRECATED_STATUS_MAP'][order['status']] if order['status'] in app.config['DEPRECATED_STATUS_MAP'] else order['status']
                item_dict['order_id'] = str(order['_id'])
                item_dict['real_order_id'] = order['order_id'] if 'order_id' in order else None
                item_dict['user_id'] = order['user_id']
                item_dict['total_price'] = order['total_price'] if 'total_price' in order else 0
                item_dict['created_date'] = order['created_date']
                item_dict['pickup_id'] = str(order['pickup_id'])
                item_dict['delivery_id'] = str(order['delivery_id'])
                item_dict['racks'] = order['racks'] if 'racks' in order else []
                item_dict['address_id'] = order['address_id']
                item_dict['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
                item_dict['cash_collected'] = order.get('cash_collected', 0)

                item_dict['last_credit_used'] = order.get('last_credit_used', 0)

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

    def post(self):
        order_id = None
        data = self.base_order()

        form = copy.deepcopy(request.form)
        if 'address_id' not in form or not form['address_id']:
            return {'status': "failure", 'error': "Address id not provided."}, 403

        if 'pickup_time' not in form or not form['pickup_time']:
            return {'status': "failure", 'error': "Pickup time not provided."}, 403

        if 'schedule_time' not in form or not form['schedule_time']:
            return {'status': "failure", 'error': "Delivery time not provided."}, 403

        if 'pickup_date_submit' not in form or not form['pickup_date_submit']:
            return {'status': "failure", 'error': "Pickup date not provided."}, 403

        if 'schedule_date_submit' not in form or not form['schedule_date_submit']:
            return {'status': "failure", 'error': "Delivery date not provided."}, 403

        if 'phone' not in form or not form['phone']:
            return {'status': "failure", 'error': "Phone number not provided."}, 403

        if 'user_id' not in form or not form['user_id']:
            return {'status': "failure", 'error': "user id not provided."}, 403
        
        pickup_schedule = self.base_schedule()
        delivery_schedule = self.base_schedule()

        pickup_schedule["address_id"] = form.get("address_id")
        delivery_schedule["address_id"] = form.get("address_id")

        pickup_schedule["is_pickup"] = True
        delivery_schedule["is_pickup"] = False

        pickup_schedule["schedule_time"] = TIMESLOTS[str(form.get("pickup_time"))]
        pickup_schedule["schedule_date"] = form.get("pickup_date_submit")
        pickup_schedule["schedule_date_new"] = datetime.strptime(form.get("pickup_date_submit"), "%Y/%m/%d")

        delivery_schedule["schedule_time"] = TIMESLOTS[str(form.get("schedule_time"))]
        
        if form.getlist("schedule_date_submit")[0] != "":
            delivery_schedule["schedule_date"] = form.getlist("schedule_date_submit")[0]
            delivery_schedule["schedule_date_new"] = datetime.strptime(form.getlist("schedule_date_submit")[0], "%Y/%m/%d")
        else:
            delivery_schedule["schedule_date"] = form.getlist("schedule_date_submit")[1]

        pickup_schedule["is_completed"] = False
        delivery_schedule["is_completed"] = False

        pickup_schedule["is_active"] = True
        delivery_schedule["is_active"] = True
        service_type = None
        if 'service' in form and form.get('service'):
            service_type = form.get("service")
        
        coupon_result = None
        coupon_name = None
        user_id = None
        if 'coupon' in form and form.get('coupon'):
            coupon_name = form.get("coupon")
        if 'user_id' in form and form.get("user_id"):
            user_id = form.get("user_id")

        is_coupon_valid = False
        result_map = {}
        if coupon_name and user_id and service_type:
            result_map = self._coupon_verify(coupon_name,user_id,service_type)
            if isinstance(result_map, tuple):
                result_map = result_map[0]
            if result_map['status'] == 'success':
                is_coupon_valid = True
            else:
                return result_map, 403

        user_order_coupon_result = ""
        if is_coupon_valid:
            try:
                coupon_result = CouponModel.query.filter(
                    CouponModel.data['name'].astext == coupon_name.lower()
                ).first()
            except Exception, e:
                print e
                return {'status': 'failure', 'error': "coupon db error"}, 500
        
            data["coupon"] = {
                'name': coupon_name,
                'str_id': coupon_result.str_id
            }
            data['discount'] = {
                'amount': coupon_result.data['amount'] if 'amount' in coupon_result.data else 0,
                'max': int(coupon_result.data['max']) if 'max' in coupon_result.data else 0,
                'percentage': coupon_result.data['percentage'] if 'percentage' in coupon_result.data else False,
                'min_order': int(coupon_result.data['min_order']) if 'min_order' in coupon_result.data else 0
            }

        try:
            data["pickup_id"] = db.schedules.insert(pickup_schedule)
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "some error occured"}, 500
        
        try:
            data["delivery_id"] = db.schedules.insert(delivery_schedule)
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "some error occured"}, 500
        
        data["special_instructions"] = form.get("special_instructions")
        data["address_id"] = form.get("address_id")
        data["service_type"] = service_type

        data["user_id"] = form.get("user_id")
        data["phone"] = form.get("phone")
        data["type"] = form.get("washtypes").split(",")
        data['last_credit_used'] = 0
        data["order_id"] = 'EX' + data["order_id"] if data["service_type"] == "express" else data["order_id"]
        data['status_timestamp'] = {data['status']: datetime.utcnow()}

        try:
            db.users.update({
                'user_id': data["user_id"]
                }, {
                '$set': {
                        "phone": data['phone'],
                        "user_id": data["user_id"],
                        'updatedAt': datetime.now()
                    }
                }
            )
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "db error occured"}, 500

        try:
            order_id = db.orders.insert(data)
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "db error occured while creating order"}, 500

        if is_coupon_valid:
            try:
                user_order_coupon_result = UserOrderCouponModel()
                user_id = str(db.users.find_one({"user_id": user_id})["_id"])
                user_order_coupon_result.user = str(user_id)
                user_order_coupon_result.coupon = str(coupon_result.str_id)
                user_order_coupon_result.order = str(order_id)
                pgdb.session.add(user_order_coupon_result)
                pgdb.session.commit()
            except Exception, e:
                print e
                return {'status': 'failure', 'error': "db error occured"}, 500

        # Assign hub for the order asyncronously by using its address
        try:
            arequests.put(app.config['SERVER_SELF'] + "/api/address/" + data["address_id"], data={'refresh_hub': 'true'})
        except Exception, e:
            pass

        try:
            user = db.users.find_one({'user_id': data['user_id']})
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "some error occured"}, 500

        if order_id:
            if 'email' in user:
                emails.email_order_placed({
                    'order_id': str(order_id),
                    'email': user['email'],
                    'name': user['name']
                })

            if form.get("pickup_date_submit") == "2015/08/22":
                emails.election_closing_sms({
                    'order_id': str(order_id),
                    'name': user['name']
                })
            else:
                emails.sms_order_placed({
                    'order_id': str(order_id),
                    'name': user['name']
                })

        return {'status': 'success', '_id': str(order_id)}

    def put(self, order_id):
        global STATUSES

        if not order_id:
            return {'status': 'failure', 'error': 'Please provide order id.'}, 403

        real_order_id = None
        if len(order_id) < 15:
            real_order_id = order_id

        form = copy.deepcopy(request.form)

        set_dict = {
            'failure_reason': {
                'pickup': None,
                'delivery': None,
                'partial_payment': None
            }
        }

        # for pickups #
        order = None
        if 'bags' in form:
            try:
                if real_order_id is None:
                    order = db.orders.find_one({'_id': bson.ObjectId(order_id)})
                else:
                    order = db.orders.find_one({'order_id': real_order_id})

                pickup = db.schedules.find_one({'_id': order['pickup_id']})
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
            try:
                bags = json.loads(form['bags'])
            except Exception, e:
                return {'status': 'failure', 'error': 'Invalid json format for bags.'}, 403

            # Check if bag already used for the day
            if bags[0]['action'] == 'add':
                current_date = pickup['schedule_date']
                pickup_ids = []
                all_bags = []
                for bag in bags:
                    all_bags += bag['name']
                try:
                    schedules = db.schedules.find({'schedule_date': current_date, 'is_pickup': True})
                    for schedule in schedules:
                        pickup_ids.append(schedule['_id'])
                    orders = db.orders.find({
                        'pickup_id': {'$in': pickup_ids},
                        '$or': [
                            {'bag.laundry': {'$in': all_bags}},
                            {'bag.dryclean': {'$in': all_bags}},
                            {'bag.iron': {'$in': all_bags}}
                        ]
                    })
                except Exception, e:
                    print e
                    return {'status': 'failure', 'error': 'db error.'}, 500

                if orders.count():
                    existing_bag_set = []
                    for bag_order in orders:
                        existing_bag_set += bag_order['bag'].get('laundry', []) + bag_order['bag'].get('dryclean', []) + bag_order['bag'].get('iron', [])
                        existing_bag_set = set(existing_bag_set)
                        all_bags = set(all_bags)
                        duplicate_bags = list(all_bags.intersection(existing_bag_set))
                    return {'status': 'failure', 'error': 'Bag already exists.', 'duplicate_bags': duplicate_bags}, 403

            if 'bag' not in order:
                order['bag'] = {}
            for bag in bags:
                if bag['type'] == 'laundry':
                    laundry_bags = set(order['bag']['laundry']) if 'laundry' in order['bag'] else set(  )
                    for item in bag['name']:
                        if bag['action'] == 'add':
                            laundry_bags.add(item)
                        elif bag['action'] == 'remove':
                            try:
                                laundry_bags.remove(item)
                            except KeyError, e:
                                raise e
                    set_dict['bag.laundry'] = list(laundry_bags)
                elif bag['type'] == 'dryclean':
                    dryclean_bags = set(order['bag']['dryclean']) if 'dryclean' in order['bag'] else set()
                    for item in bag['name']:
                        if bag['action'] == 'add':
                            dryclean_bags.add(item)
                        elif bag['action'] == 'remove':
                            try:
                                dryclean_bags.remove(item)
                            except KeyError, e:
                                pass
                    set_dict['bag.dryclean'] = list(dryclean_bags)
                elif bag['type'] == 'iron':
                    iron_bags = set(order['bag']['iron']) if 'iron' in order['bag'] else set()
                    for item in bag['name']:
                        if bag['action'] == 'add':
                            iron_bags.add(item)
                        elif bag['action'] == 'remove':
                            try:
                                iron_bags.remove(item)
                            except KeyError, e:
                                pass
                            
                    set_dict['bag.iron'] = list(iron_bags)

        if 'pickup_sheet_printed' in form:
            set_dict['pickup_sheet_printed'] = form['pickup_sheet_printed']

        if 'cash_collected' in form:
            try:
                set_dict['cash_collected'] = int(form['cash_collected'])
            except Exception, e:
                return {'status': 'failure', 'error': 'cash_collected must be a number.'}, 403

        if 'estimated_quantity' in form:
            estimated_quantity = json.loads(form['estimated_quantity'])
            for item in estimated_quantity:
                if item.get('type', '') not in ['laundry', 'dryclean', 'iron']:
                    return {'status': 'failure', 'error': 'Service type not provided.'}, 403

                if not str(item.get('quantity', '')):
                    return {'status': 'failure', 'error': 'Quantity not provided.'}, 403

                set_dict['estimated_quantity.' + item['type']] = int(item['quantity'])

        # for delivery #
        if 'is_paid' in form:
            if form['is_paid'] == "paid":
                set_dict['is_paid'] = "paid"
            elif form['is_paid'] == "not_paid":
                set_dict['is_paid'] = "not_paid"
            elif form['is_paid'] == "partially_paid":
                set_dict['is_paid'] = "partially_paid"
            elif form['is_paid'] == "excess_paid":
                set_dict['is_paid'] = "excess_paid"

            try:
                if real_order_id is None:
                    order = db.orders.find_one({'_id': bson.ObjectId(order_id)})
                else:
                    order = db.orders.find_one({'order_id': real_order_id})
            except Exception, e:
                traceback.print_exc(file=sys.stdout)
                return {'status': 'failure', 'error': 'db error.'}, 500
            try:
                user = db.users.find_one({'user_id': order['user_id']})
            except Exception, e:
                return {'status': 'failure', 'error': "db error"}, 500

            cash_collected = int(form['cash_collected'])
            available_credits = user['credits'] if 'credits' in user else 0
            total_price = order['total_price'] if 'total_price' in order else 0

            txn = None
            if order.get('payment_id', False):
                txn = OnlineTransaction.query.filter(
                    OnlineTransaction.str_id == order['payment_id']
                ).first()
            else:
                txn = OnlineTransaction()
            txn.txn_date = datetime.now()
            txn.data = {
                'SERVICE': 'COD',
                'TOTALAMT': total_price,
                'TXNAMT': cash_collected,
                'PAYMENTMODE': 'CASH',
                'STATUS': form['is_paid'].upper()
            }
            txn.txn_type = 'cod'
            try:
                pgdb.session.add(txn)
                pgdb.session.commit()
            except Exception, e:
                return {'status': 'failure', 'error': 'payment db error'}, 500

            set_dict['payment_id'] = txn.str_id

            if set_dict['is_paid'] == "excess_paid":
                old_last_credit_used = order['last_credit_used'] if 'last_credit_used' in order else 0
                new_available_credits = available_credits + (cash_collected - int(total_price) - int(old_last_credit_used))
                try:
                    db.users.update({
                        'user_id': order["user_id"]
                    }, {
                        '$set': {
                            'credits': new_available_credits
                        }
                    })
                    
                except Exception, e:
                    print e
                    return {'status': 'failure', 'error': "db error"}, 500

                set_dict['last_credit_used'] = cash_collected - total_price

        if 'invoice_printed' in form:
            set_dict['invoice_printed'] = form['invoice_printed']

        if 'is_pickup' in form:
            set_dict['is_pickup'] = form['is_pickup']

        if 'assigned_to' in form:
            set_dict['assigned_to'] = form['assigned_to']

        if 'failure_reason' in form:
            try:
                failure = json.loads(form['failure_reason'])
            except Exception, e:
                return {'status': 'failure', 'error': 'Invalid json format.'}, 403

            if 'type' not in failure:
                return {'status': 'failure', 'error': 'Reason type not provided.'}, 403
            # elif failure['type'] not in ['pickup', 'delivery', 'partial_payment']:
                # return {'status': 'failure', 'error': 'Reason type incorrect.'}, 403

            reason = None
            if 'type2' in failure and failure['type2'] == 'other':
                reason = Reason()
                reason.data = {'reason': failure['reason']}
                pgdb.session.add(reason)
                try:
                    pgdb.session.commit()
                except Exception as e:
                    return {'status': 'failure', 'error': 'db error.'}, 500
            else:
                try:
                    reason = Reason.query.filter(Reason.str_id == failure['reason']).first()
                except Exception, e:
                    return {'status': 'failure', 'error': 'db error.'}, 500
            set_dict['failure_reason'][failure['type']] = reason.str_id

        if 'racks' in form:
            try:
                data = json.loads(form['racks'])
            except Exception, e:
                return {'status': 'failure', 'error': 'Racks not in proper json format.'}, 403

            racks = data['racks']
            rack_type = data['type']

            try:
                # Check if the rack is already filled
                rack_order = False
                if racks:
                    rack_order = db.orders.find_one({
                        'status': 'washing',
                        '$or': [
                            {'racks.laundry': {'$in': racks}},
                            {'racks.dryclean': {'$in': racks}},
                            {'racks.iron': {'$in': racks}}
                        ]
                    })
                if rack_order:
                    if str(rack_order['_id']) != order_id:
                        return {'status': 'failure', 'error': 'Rack already filled. Choose another rack.'}, 403

                if rack_type == 'laundry':
                    set_dict['racks.laundry'] = racks

                if rack_type == 'dryclean':
                    set_dict['racks.dryclean'] = racks

                if rack_type == 'iron':
                    set_dict['racks.iron'] = racks

            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500

        query = {}
        if set_dict:
            query['$set'] = set_dict
            if 'status' in set_dict and set_dict['status'] == 'order_cancelled':
                try:
                    user_order_coupon = UserOrderCouponModel.query.filter(UserOrderCouponModel.order == str(order_id)).first()
                    if user_order_coupon and user_order_coupon.is_active:
                        user_order_coupon.is_active = False
                        pgdb.session.commit()
                except Exception, e:
                    return {'status': 'failure', 'error': 'db error.'}, 500
        else:
            return {'status': 'failure', 'error': 'No parameter provided.'}, 403

        order = None
        send_status_message = True
        # DELIVERY PROGRESS STATUS PROCESS
        if 'status' in form:
            status = form['status']
            if status not in STATUSES:
                return {'status': 'failure', 'error': 'Given status is incorrect.'}, 403
            try:
                if real_order_id is None:
                    order = db.orders.find_one({'_id': bson.ObjectId(order_id)})
                else:
                    order = db.orders.find_one({'order_id': real_order_id})
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500

            if not (form['status'] == 'delivery_progress' and (order['status'] in ['delivery_failed', 'delivery_progress'])):
                query['$set']['status'] = status
            else:
                send_status_message = False

            if 'status' in set_dict:
                set_dict['status_timestamp.%s' % status] = datetime.utcnow()

        # Update the collected data
        try:
            if real_order_id is None:
                db.orders.update({'_id': bson.ObjectId(order_id)}, query)
            else:
                db.orders.update({'order_id': real_order_id}, query)
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            return {'status': 'failure', 'error': 'db error.'}, 500

        if 'status' in form and form['status']:
            message = ""
            try:
                delivery = db.schedules.find_one({'_id': order['delivery_id']})
                user = db.users.find_one({'user_id': order['user_id']})
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500

            # Send message on delivery progress
            if form['status'] == 'delivery_progress' and send_status_message:
                subs = {
                    'name': user.get('name', 'Customer').capitalize(),
                    'amount': order.get('total_price', '0'),
                    'slot': delivery.get('schedule_time').replace(' ', '')
                }
                message = "Hi %(name)s, your clothes are out for delivery & will reach you between %(slot)s today. Your invoice amount is INR %(amount)s. Thanks for using MyWash." % subs

            # Send message on failed pickup
            elif form['status'] == 'pickup_failed':
                try:
                    reason = Reason.query.filter(Reason.str_id == form['failure_reason']['reason']).first()
                except Exception, e:
                    pass
                subs = {
                    'name': user.get('name', 'Customer').capitalize(),
                    'reason': reason.data.get('reason', '')
                }
                message = "Hi %(name)s, we have attempted your pickup today but the attempt was unsuccessful due to the reason: %(reason)s. The pickup will be attempted tomorrow again on priority." % subs

            # Send message on failed delivery
            elif form['status'] == 'delivery_failed':
                print form
                try:
                    reason = Reason.query.filter(Reason.str_id == form['failure_reason']['reason']).first()
                except Exception, e:
                    pass
                subs = {
                    'name': user.get('name', 'Customer').capitalize(),
                    'reason': reason.data.get('reason', '')
                }
                message = "Hi %(name)s, we have attempted your delivery today but the attempt was unsuccessful due to the reason: %(reason)s. The delivery will be attempted tomorrow again on priority." % subs

            if message != "":
                emails.mywash_order_transactional_sms(
                    order.get('phone'),
                    message,
                    order.get('partner_id', None)
                )
        return {'status': 'success'}


class OrderSearch(Resource):
    def get(self, **kwargs):
        term = kwargs.get('term', None)
        skip = kwargs.get('skip', 0)
        limit = kwargs.get('limit', 20)
        status = kwargs.get('status', None)

        if not term:
            return {"status": 'failure', 'error': 'no search term provided.'}, 403

        term_split = term.split(":")

        if term_split[0].lower() not in SEARCH_OPTIONS:
            return {"status": 'failure', 'error': '"%s" is not a valid search criteria.' % term_split[0]}, 403

        if len(term_split) < 2:
            return {"status": 'failure', 'error': 'not enough search arguments.'}, 403

        search_arg = ":".join(term_split[1:])
        search_arg = search_arg.strip()

        if not search_arg:
            return {"status": 'failure', 'error': 'not enough search arguments.'}, 403

        if term_split[0] == 'oid':
            order = db.orders.find_one(
                {'order_id': search_arg},
                {'order': 1, 'user_id': 1, 'total_price': 1, 
                    'status': 1, 'created_date': 1, 'order_id': 1,
                    'delivery_id': 1, 'pickup_id': 1, 'updated_date': 1, 'racks': 1, 'address_id': 1,
                    'cash_collected':1},
            )
            if not order:
                return {'status': 'failure', 'error': 'order id doesn\'t exist'}, 403
                
            user = db.users.find_one(
                {'user_id': order['user_id']},
                {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1, 'email': 1, 'phone': 1},
            )
            schedules = db.schedules.find(
                {'_id': {'$in': [order['delivery_id'], order['pickup_id']]}},
                {'user_id': 0, '_id': 0, 'created_date': 0}
            )
            for schedule in schedules:
                schedule['updated-date'] = str(schedule['updated-date'])
                if schedule['is_pickup']:
                    order['pickup_data'] = schedule
                else:
                    order['delivery_data'] = schedule
            order['delivery_id'] = str(order['delivery_id'])
            order['pickup_id'] = str(order['pickup_id'])
            order['updated_date'] = str(order['updated_date'])

            user['_id'] = str(user['_id'])
            order['_id'] = str(order['_id'])
            order['real_order_id'] = order['order_id'] if 'order_id' in order else None
            order['order_id'] = order['_id']
            order['user_info'] = user
            order['racks'] = order['racks'] if 'racks' in order else []
            order['total_price'] = order['total_price'] if 'total_price' in order else 0
            order['status'] = app.config['DEPRECATED_STATUS_MAP'][order['status']] if order['status'] in app.config['DEPRECATED_STATUS_MAP'] else order['status']
            order['cash_collected'] = order.get('cash_collected', 0)
            if order['cash_collected'] == order['total_price']:
                order['paid'] = 'paid'
            elif order['cash_collected'] > order['total_price']:
                order['paid'] = 'excess_paid'
            else:
                order['paid'] = 'other'

            address = db.addresses.find_one({'_id': bson.ObjectId(order['address_id'])})
            if 'assigned_hub' in address:
                order['hub'] = HUBS[address['assigned_hub']]
            else:
                order['hub'] = HUBS[1]
            
            return jsonify({'data': [order]})
        
        else:
            match_pipe = {}
            if term_split[0] == 'email':
                match_pipe['email'] = re.compile(search_arg, re.IGNORECASE)
            elif term_split[0] == 'name':
                match_pipe['name'] = re.compile(search_arg, re.IGNORECASE)
            elif term_split[0] == 'phone':
                search_arg = "^" + search_arg
                match_pipe['phone'] = re.compile(search_arg, re.IGNORECASE)

            aggregate_query = [
                {'$project': {'_id': 1, 'name': 1, 'pictureUrl': 1, 'user_id': 1, 'email': 1, 'phone': 1}},
                {'$match': match_pipe},
            ]

            try:
                users = db.users.aggregate(aggregate_query)
            except Exception, e:
                return {'status': 'failure', 'error': "some error occured"}, 500

            users_dict = {}
            for user in users['result']:
                user['_id'] = str(user['_id'])
                users_dict[user['user_id']] = user

            order_match_pipe = {}
            if status == 'cancelled':
                order_match_pipe['status'] = {'$in': [5, 6, 'order_cancelled', 'order_rejected']}
            elif status == 'completed':
                order_match_pipe['status'] = {'$in': [4, "clothes_delivered"]}
            elif status == 'package':
                order_match_pipe['status'] = {'$in': ["washing"]}

            order_match_pipe['user_id'] = {'$in': users_dict.keys()}

            aggregate_query = [
                {'$project': {'user_id': 1, 'total_price': 1, 'order_id': 1,
                    'status': 1, 'order_items': 1, 'created_date': 1,
                    'delivery_id': 1, 'pickup_id': 1, 'racks': 1, 'address_id': 1}},
                {
                    '$match': order_match_pipe
                },
                {'$sort': {'created_date': -1}},
                {'$skip': skip},
                {'$limit': limit}
            ]

            try:
                orders = db.orders.aggregate(aggregate_query)
            except Exception, e:
                return {'status': 'failure', 'error': "some error occured"}, 500

            orders = orders['result']

            schedule_ids = []
            address_ids = []
            for order in orders:
                order['_id'] = str(order['_id'])
                order['real_order_id'] = order['order_id'] if 'order_id' in order else None
                order['order_id'] = str(order['_id'])
                order['user_info'] = users_dict[order['user_id']]
                order['service_type'] = order['service_type'] if 'service_type' in order else 'regular'
                order['total_price'] = order['total_price'] if 'total_price' in order else 0
                order['status'] = app.config['DEPRECATED_STATUS_MAP'][order['status']] if order['status'] in app.config['DEPRECATED_STATUS_MAP'] else order['status']
                order['total_price'] = order['total_price'] if 'total_price' in order else 0
                order['racks'] = order['racks'] if 'racks' in order else []
                schedule_ids.append(order['pickup_id'])
                schedule_ids.append(order['delivery_id'])

                address_ids.append(bson.ObjectId(order['address_id']))

                order['pickup_id'] = str(order['pickup_id'])
                order['delivery_id'] = str(order['delivery_id'])

            try:
                schedules = db.schedules.find(
                    {'_id': {'$in': schedule_ids}},
                    {'user_id': 0, 'created_date': 0}
                )
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500

            schedule_data = {}
            for schedule in schedules:
                schedule['updated-date'] = str(schedule['updated-date'])
                schedule['_id'] = str(schedule['_id'])
                schedule_data[schedule['_id']] = schedule

            try:
                addresses = db.addresses.find({
                    '_id': {'$in': address_ids}
                })
            except Exception, e:
                return {'status': 'failure', 'error': 'db error'}, 500

            address_dict = {}
            for address in addresses:
                if 'assigned_hub' in address:
                    address_dict[str(address['_id'])] = address['assigned_hub']

            for order in orders:
                order['pickup_data'] = schedule_data[order['pickup_id']]
                order['delivery_data'] = schedule_data[order['delivery_id']]
                if order['address_id'] in address_dict:
                    order['hub'] = HUBS[address_dict[order['address_id']]]
                else:
                    order['hub'] = HUBS[1]

            return jsonify({'data': orders})


class OrderHistory(Resource):
    def get(self, user_id):
        try:
            orders = list(db.orders.find({'user_id': user_id}, {'order_items': 0, 'invoice': 0}).sort('created_date', -1))
        except Exception, e:
            print e
            return {"status": "failure", "error": "db error"}

        pickup_list = []
        delivery_list = []
        pickup_dict = {}
        delivery_dict = {}
        hub_list = set()
        address_list = set()

        for order in orders:
            order['_id'] = str(order['_id'])
            pickup_list.append(order['pickup_id'])
            delivery_list.append(order['delivery_id'])
            order['status'] = app.config['DEPRECATED_STATUS_MAP'][order['status']] if order['status'] in app.config['DEPRECATED_STATUS_MAP'] else order['status']
            order['pickup_id'] = str(order['pickup_id'])
            order['delivery_id'] = str(order['delivery_id'])
            if not isinstance(order['type'], list) and order['type']:
                order['type'] = [app.config['SERVICE_TYPE_MAP'][order['type']]]
            address_list.add(order['address_id'])

        # Get the addresses
        try:
            addresses = db.addresses.find({'_id': {'$in': list(address_list)}})
        except Exception, e:
            print e
            return {"status": "failure", "error": "db error"}, 500
        address_dict = {}
        for address in addresses:
            if 'assigned_hub' in address:
                address_dict[str(address['_id'])] = address['assigned_hub']
                hub_list.add(address['assigned_hub'])

        # Get the hubs
        hubs = []
        if hub_list:
            try:
                hubs = MywashHub.query.filter(MywashHub.id.in_(list(hub_list)))
            except Exception, e:
                print e
                return {"status": "failure", "error": "db error"}, 500
        hubs_dict = {}
        for hub in hubs:
            hubs_dict[hub.id] = copy.deepcopy(hub.data)

        # Get the pickupes
        try:
            pickups = db.schedules.aggregate([
                {'$match': {'is_pickup': True, '_id': {'$in': pickup_list}}}
            ])
        except Exception, e:
            print e
            return {"status": "failure", "error": "db error"}, 500

        for pickup in pickups['result']:
            pickup['_id'] = str(pickup['_id'])
            pickup['updated-date'] = pickup['updated-date'].strftime("%Y-%m-%d %H:%M:%S%Z")
            pickup_dict[pickup['_id']] = pickup

        # Get the deliveries
        try:
            deliveries = db.schedules.aggregate([
                {'$match': {'is_pickup': False, '_id': {'$in': delivery_list}}}
            ])
        except Exception, e:
            print e
            return {"status": "failure", "error": "db error"}

        for delivery in deliveries['result']:
            delivery['_id'] = str(delivery['_id'])
            delivery['updated-date'] = delivery['updated-date'].strftime("%Y-%m-%d %H:%M:%S%Z")
            delivery_dict[delivery['_id']] = delivery

        for order in orders:
            order['pickup_data'] = pickup_dict[order['pickup_id']] if order['pickup_id'] in pickup_dict else None
            order['delivery_data'] = delivery_dict[order['delivery_id']]
            if order['address_id'] in address_dict and address_dict[order['address_id']]:
                order['assigned_hub'] = hubs_dict.get(address_dict[order['address_id']], None)
        return jsonify({'data': orders})


class OrderAgent(Resource):
    def get(self, **kwargs):
        try:
            agent_id = kwargs.get('agent_id', None)
            date = kwargs.get('date', None)
            if agent_id is None:
                return {'status': 'failure', 'error': 'Agent id not provided.'}, 403
            if date is None:
                return {'status': 'failure', 'error': 'Date not provided.'}, 403
            query = {
                'assigned_to': agent_id,
                'schedule_date': datetime.strptime(date, "%Y-%m-%d").strftime("%Y/%m/%d")
            }
            try:
                schedules = db.schedules.find(query).sort('schedule_time', 1)
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
            schedule_ids = []
            schedule_data = {}
            for schedule in schedules:
                schedule_ids.append(schedule['_id'])
                schedule['_id'] = str(schedule['_id'])
                schedule_data[schedule['_id']] = schedule
            order_query = {
                '$and': [{
                    '$or': [
                        {'pickup_id': {'$in': schedule_ids}},
                        {'delivery_id': {'$in': schedule_ids}}
                    ],
                    'status': {'$nin': ['order_cancelled', 'order_rejected', 'delivery_ready', 'washing', 'order_placed']}
                }]
            }
            try:
                orders = list(db.orders.find(order_query))
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
            user_ids = []
            address_ids = []
            for order in orders:
                order['_id'] = str(order['_id'])
                order['pickup_id'] = str(order['pickup_id'])
                order['delivery_id'] = str(order['delivery_id'])
                if str(order['pickup_id']) in schedule_data and order['status'] in ['pickup_progress', 'pickup_failed', 'pickup_success']:
                    order['pickup_data'] = schedule_data[str(order['pickup_id'])]
                elif str(order['delivery_id']) in schedule_data and order['status'] in ['delivery_progress', 'delivery_failed', 'clothes_delivered']:
                    order['delivery_data'] = schedule_data[str(order['delivery_id'])]
                user_ids.append(order['user_id'])
                address_ids.append(bson.ObjectId(order['address_id']))
            try:
                users = list(db.users.find(
                    {'user_id': {'$in': user_ids}},
                    {'user_id': 1, 'name': 1, 'email': 1}
                ))
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
            users_dict = {}
            for user in users:
                user['_id'] = str(user['_id'])
                users_dict[user['user_id']] = user
            try:
                addresses = list(db.addresses.find({'_id': {'$in': address_ids}}))
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
            address_dict = {}
            for address in addresses:
                address['_id'] = str(address['_id'])
                address_dict[address['_id']] = address
            for order in orders:
                try:
                    order['user_data'] = users_dict[order['user_id']]
                    order['address_data'] = address_dict[order['address_id']]
                except Exception, e:
                    pass
            return jsonify({'data': orders})
        except Exception as e:
            return {'status': 'failure', 'error': str(e)}
