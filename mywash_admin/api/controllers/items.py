from flask.ext.restful import Resource
from flask import jsonify, request, session
from datetime import datetime
from mywash_admin import app
import bson
import json
import copy
from api.models import Reason, OnlineTransaction

PICKUP_TYPES = [
    'order',
    'missed',
    'rescheduled'
]

db = app.config['MONGO_CLIENT']['dealsup']

redis_conn = app.config['REDIS_CLIENT']


class OrderItems(Resource):
    def get(self, order_id=None):
        order_details = None
        order = db.orders.find_one({'_id': bson.ObjectId(order_id)})

        if 'order_items' in order and order['order_items']:
            order_details = order['order_items']
        else:
            order_details = [item for item in db.items.find({'isActive': True}, {'_id': 0})]

        user = db.users.find_one({'user_id': order['user_id']})

        schedules = list(db.schedules.find({
                '_id': {'$in': [order['delivery_id'], order['pickup_id']]}
            },
            {'_id': 0, 'address_id': 0, 'is_active': 0, 'user_id': 0, 'updated-date': 0, 'is_completed': 0, 'agent_id': 0, 'created_date': 0}
        ))

        address = db.addresses.find_one(
            {'_id': bson.ObjectId(order['address_id'])},
            {'is_active': 0, 'tag': 0, 'latitude': 0, 'longitude': 0, '_id': 0, 'user_id': 0}
        )

        final_schedule = {}
        for schedule in schedules:
            if schedule['is_pickup']:
                final_schedule['pickup'] = schedule
            else:
                final_schedule['delivery'] = schedule

        reason_ids = []
        if 'failure_reason' in order:
            for reason in order['failure_reason'].values():
                if reason is not None:
                    reason_ids.append(reason)

        if reason_ids:
            reasons_dict = {}
            try:
                reasons = Reason.query.filter(Reason.str_id.in_(reason_ids)).all()
                for reason in reasons:
                    reasons_dict[reason.str_id] = {
                        'full_reason': reason.data['reason'],
                        'reason': reason.str_id
                    }

                for key, value in order['failure_reason'].items():
                    if order['failure_reason'][key] is not None:
                        order['failure_reason'][key] = reasons_dict[order['failure_reason'][key]]
            except Exception, e:
                print e
                # return {'status': 'failure', 'error': 'db error.'}, 500
                pass

        if 'is_paid' in order:
            if isinstance(order['is_paid'], bool):
                order['is_paid'] = 'paid' if order['is_paid'] else 'not_paid'
        else:
            order['is_paid'] = False

        payment = {
            'id': None,
            'type': None
        }
        if order.get('payment_id', False):
            try:
                transaction = OnlineTransaction.query.filter(
                    OnlineTransaction.str_id == order['payment_id'],
                    OnlineTransaction.is_active == True
                ).first()
            except Exception, e:
                pass

            if transaction:
                payment['id'] = transaction.str_id
                try:
                    payment['service'] = transaction.data.get('SERVICE', '').lower()
                except Exception, e:
                    payment['service'] = ''
                payment['type'] = transaction.txn_type

        other_info = {
            '_id': order_id,
            'schedules': final_schedule,
            'address': address,
            'created_date': order['created_date'],
            'user': {
                'name': user['name'],
                'phone': order['phone'] if 'phone' in order else '',
                'email': user['email'] if 'email' in user else '',
                'credits': user['credits'] if 'credits' in user else 0,
                'pictureUrl': user['pictureUrl'],
                'partner_id': user.get('partner', {}).get('id', '') if 'partner' in user else '',
            },
            'cost': {
                'total': order['total_price'] if 'total_price' in order else 0,
                'sub_total': order['sub_total_price'] if 'sub_total_price' in order else 0
            },
            'credits': order['credits'] if 'credits' in order else {},
            'remark': order['remark'] if 'remark' in order else None,
            'discount': order['discount'] if 'discount' in order else {},
            'status': order['status'],
            'order_id': order['order_id'] if 'order_id' in order else None,
            'bag': order['bag'] if 'bag' in order else {},
            'is_paid': order['is_paid'],
            'racks': order['racks'] if 'racks' in order else [],
            'failure_reason': order['failure_reason'] if 'failure_reason' in order else {},
            'cash_collected': order['cash_collected'] if 'cash_collected' in order else 0,
            'service_type': order['service_type'] if 'service_type' in order else '',
            'wash_type': order.get('type', []),
            'last_credit_used': order['last_credit_used'] if 'last_credit_used' in order else 0,
            'service_tax': order['service_tax'] if 'service_tax' in order else {},
            'coupon': order['coupon'] if 'coupon' in order else {},
            'payment': payment
        }
        return jsonify({'data': order_details, 'customer_details': other_info})
        
    def post(self, order_id):
        form = copy.deepcopy(request.form)
        data = json.loads(form.get('data', '[]'))
        remark = form.get('remark', None)
        discount = json.loads(form.get('discount', '{}'))
        order = None
        pickup = None
        new_available_credits = None

        try:
            order = db.orders.find_one({'_id': bson.ObjectId(order_id)})
            pickup = db.schedules.find_one({'_id': order['pickup_id']})
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        if discount:
            discount['amount'] = int(discount['amount']) if 'amount' in discount else 0
            discount['max'] = int(discount['max']) if 'max' in discount else 0
            discount['min_order'] = int(discount['min_order']) if 'min_order' in discount else 0

        sub_total_cost = 0.0
        service_tax = 0
        # Get total cost
        if data:
            for item in data:
                if 'quantity' not in item:
                    continue
                if 'laundry' in item['quantity'] and item['price']['laundry'] != "NA":
                    sub_total_cost += int(item['price']['laundry']) * int(item['quantity']['laundry'])
                if 'dryclean' in item['quantity'] and item['price']['dry_cleaning'] != "NA":
                    sub_total_cost += int(item['price']['dry_cleaning']) * int(item['quantity']['dryclean'])
                if 'iron' in item['quantity'] and item['price']['iron'] != "NA":
                    sub_total_cost += int(item['price']['iron']) * int(item['quantity']['iron'])

            if 'service_type' in order and order['service_type'] == 'express':
                sub_total_cost *= 2

            total_discount = 0
            if 'percentage' in discount and discount['percentage']:
                if 'min_order' in discount and discount['min_order']:
                    if discount['min_order'] <= sub_total_cost:
                        total_discount = sub_total_cost * discount['amount'] / 100
                else:
                    total_discount = sub_total_cost * discount['amount'] / 100
            else:
                if 'min_order' in discount and discount['min_order']:
                    if discount['min_order'] <= sub_total_cost:
                        total_discount = discount.get('amount', 0)
                else:
                    total_discount = discount.get('amount', 0)

            if 'max' in discount and discount['max']:
                if total_discount > discount['max']:
                    total_discount = discount['max']

            total_cost = sub_total_cost - total_discount

            if pickup['schedule_date_new'] >= datetime(2015, 07, 18):
                if redis_conn.hget('SERVICE_TAX', 'type') == 'inclusive':
                    service_tax = int(round(total_cost * int(redis_conn.hget('SERVICE_TAX', 'rate'))/100))
                else:
                    service_tax = int(round(total_cost * int(redis_conn.hget('SERVICE_TAX', 'rate'))/100))
                    total_cost += service_tax

            print total_cost, sub_total_cost, total_discount
            discount['total'] = total_discount
            # Deduct from credits
            available_credits = None
            used_credits = None

            try:
                if 'credits' in order and 'available' in order['credits']:
                    available_credits = order['credits']['available']
                else:
                    user = db.users.find_one({'user_id': order['user_id']})
                    available_credits = user['credits'] if 'credits' in user else 0
            except Exception, e:
                pass

            if available_credits >= total_cost:
                used_credits = total_cost
                total_cost -= used_credits
                new_available_credits = available_credits - used_credits
            else:
                used_credits = available_credits
                total_cost -= used_credits
                new_available_credits = 0

        update_data = {}
        if data:
            update_data.update({
                'order_items': data,
                'total_price': int(round(total_cost)),
                'sub_total_price': int(round(sub_total_cost)),
                'discount': discount,
                'credits': {
                    'used': used_credits,
                    'available': available_credits
                },
            })
            if pickup['schedule_date_new'] >= datetime(2015, 07, 18):
                update_data.update({
                    'service_tax': {
                        'type': redis_conn.hget('SERVICE_TAX', 'type'),
                        'rate': int(redis_conn.hget('SERVICE_TAX', 'rate')),
                        'amount': service_tax
                    }
                })

        if remark:
            update_data.update({'remark': remark})

        # Update the order and update the credits
        if update_data:
            try:
                result = db.orders.update({
                    '_id': bson.ObjectId(order_id)
                }, {
                    '$set': update_data
                })

                if result['ok'] and new_available_credits is not None:
                    db.users.update({
                        'user_id': order['user_id']
                    }, {
                        '$set': {
                            'credits': new_available_credits
                        }
                    })
            except Exception, e:
                return {"error": 'db error'}, 500

        return {'status': 'success'}


class Items(Resource):
    def get(self, item_id=None):
        ret = {}
        if not item_id:
            items = db.items.find()
            item_list = []
            for item in items:
                item['_id'] = str(item['_id'])
                item_list.append(item)
            ret['items'] = item_list
        else:
            try:
                item_id = int(float(item_id))
            except ValueError, e:
                item_id = bson.ObjectId(item_id)
            ret['item'] = db.items.find_one({'_id': item_id})
            if isinstance(item_id, bson.ObjectId):
                ret['item']['_id'] = str(ret['item']['_id'])
        return ret

    def post(self):
        form = copy.deepcopy(request.form)
        update_set = {}
        update_set['price'] = {}
        
        image = form['image'].strip()
        title = form['title'].strip()
        update_set['isActive'] = True if form['is_active'] == 'yes' else False
        
        update_set['price']['dry_cleaning'] = int(form['dryclean']) if form['dryclean'] and form['dryclean'] != "NA" else "NA"
        update_set['price']['laundry'] = int(form['laundry']) if form['laundry'] and form['laundry'] != "NA" else "NA"
        update_set['price']['iron'] = int(form['iron']) if form['iron'] and form['iron'] != "NA" else "NA"
        update_set['is_visible_to_customer'] = True if form['visible_to_customer'] == 'yes' else False

        update_set['imageUrl'] = image if image and image != app.config['DEFAULT_CLOTH_PIC'] else app.config['DEFAULT_CLOTH_PIC']
        
        if title:
            update_set['title'] = title
        else:
            return jsonify({'status': "failure", 'error': "Title not available."}), 500
        
        try:
            db.items.insert(update_set)
        except Exception, e:
            return jsonify({'status': "failure", 'error': "db error."}), 500

        return jsonify({'status': "success"})

    def put(self, item_id):
        form = copy.deepcopy(request.form)
        update_set = {}
        try:
            item_id = int(float(item_id))
        except ValueError, e:
            item_id = bson.ObjectId(item_id)
        item = None
        try:
            item = db.items.find_one({'_id': item_id})
        except Exception, e:
            return jsonify({'status': "failure", 'error': "db error."}), 500

        image = form['image'].strip()
        title = form['title'].strip()
        is_active = True if form['is_active'] == 'yes' else False
        dryclean = int(form['dryclean']) if form['dryclean'] and form['dryclean'] != "NA" else "NA"
        laundry = int(form['laundry']) if form['laundry'] and form['laundry'] != "NA" else "NA"
        iron = int(form['iron']) if form['iron'] and form['iron'] != "NA" else "NA"
        visible_to_customer = True if form['visible_to_customer'] == 'yes' else False

        update_set['imageUrl'] = image if image and image != item['imageUrl'] else item['imageUrl']
        update_set['title'] = title if title != item['title'] else item['title']
        update_set['isActive'] = is_active if is_active != item['isActive'] else item['isActive']
        update_set['is_visible_to_customer'] = visible_to_customer if visible_to_customer != item['is_visible_to_customer'] else item['is_visible_to_customer']
        update_set['price'] = {}
        update_set['price']['laundry'] = laundry
        update_set['price']['dry_cleaning'] = dryclean
        update_set['price']['iron'] = iron
        try:
            db.items.update(
                {'_id': item['_id']},
                {'$set': update_set}
            )
        except Exception, e:
            return jsonify({'status': "failure", 'error': "db error."}), 500

        return jsonify({'status': "success"})
