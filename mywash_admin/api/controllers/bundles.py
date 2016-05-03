from flask.ext.restful import Resource
from flask import request
from datetime import datetime
from mywash_admin import app, db as pgdb
from flask import jsonify
import copy
from api.models import TagBundle, Vendor
import json
from mywash_admin.lib.loggers import MongoLogger

db = app.config['MONGO_CLIENT']['dealsup']
LOGGER = MongoLogger('mywash_logs', 'general_logs')
log_db = app.config['MONGO_CLIENT']['mywash_logs']


class Bundle(Resource):
    def _schema(self):
        return {
            # '_id': str(bson.ObjectId()),
            'name': None,
            'vendor': None,
            'date': None,
            'bags': []
        }

    def get(self, bundle_id):
        if not bundle_id:
            return {'status': 'failure', 'error': "Bundle id not provided."}
        
        try:
            if isinstance(bundle_id, int):
                bundle = TagBundle.query.get(bundle_id)
            else:
                bundle = TagBundle.query.filter_by(str_id=bundle_id).first()
        except Exception, e:
            raise e

        pickup_date = bundle.date.strftime("%Y/%m/%d")

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
                        '$or': [
                            {'bag.laundry': {'$in': bundle.bags}},
                            {'bag.dryclean': {'$in': bundle.bags}},
                            {'bag.iron': {'$in': bundle.bags}}
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

        user_names = {user['user_id']: user['name'] for user in users}

        user_bags = []
        for order in orders:
            for bags in order['bag'].values():
                for bag in bags:
                    if bag in bundle.bags:
                        item = {
                            'name': user_names[order['user_id']],
                            'bag': bag
                        }
                        user_bags.append(item)
        result = {
            'bags': user_bags,
            'date': bundle.date.strftime("%Y-%m-%d"),
            'name': bundle.name,
            'vendor': {'name': bundle.vendor.data["name"], 'id': bundle.vendor.id} if bundle.vendor else ""
        }

        return result
    
    def post(self):
        schema = self._schema()
        form = copy.deepcopy(request.form)

        if not form['name']:
            return {'status': 'failure', 'error': 'Bundle name not provided.'}, 403

        if not form['date']:
            return {'status': 'failure', 'error': 'Bundle date not provided.'}, 403

        if not form['bags']:
            return {'status': 'failure', 'error': 'Bundle bags not provided.'}, 403

        schema['date'] = datetime.strptime(form['date'], "%Y-%m-%d")
        schema['bags'] = json.loads(form['bags'])
        schema['name'] = form['name']
        if form['vendor']:
            try:
                schema['vendor'] = Vendor.query.get(int(form['vendor']))
            except Exception, e:
                return {'status': 'failure', 'error': 'Db error.'}, 500
        try:
            bundle = TagBundle(
                name=schema['name'],
                bags=schema['bags']
            )
            bundle.date = schema['date']
            if form['vendor']:
                bundle.vendor = Vendor.query.get(int(form['vendor']))
            pgdb.session.add(bundle)
            pgdb.session.commit()

            LOGGER.info(
                event='add_bundle',
                order_id=str(bundle.str_id),
                bundle_id=bundle.id
            )

            LOGGER.info(
                event='edit_bundle_vendor',
                order_id=str(bundle.str_id),
                vendor_id=bundle.vendor.id if bundle.vendor is not None else None,
                bundle_id=bundle.id
            )
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'Db error.'}, 500
        schema['_id'] = bundle.str_id

        return {'status': 'success', 'id': str(schema['_id'])}, 200

    def put(self, bundle_id):
        form = copy.deepcopy(request.form)
        update_data = {}

        if not len(form):
            return {'status': 'failure', 'error': 'No parameters provided.'}, 403

        if 'bags' in form:
            update_data['bags'] = json.loads(form['bags'])

        if 'date' in form:
            update_data['date'] = datetime.strptime(form['date'], "%Y-%m-%d")

        if 'name' in form:
            update_data['name'] = form['name']

        if 'vendor' in form and form['vendor']:
            update_data['vendor'] = Vendor.query.get(int(form['vendor']))

        try:
            bundle = TagBundle.query.filter(TagBundle.str_id == bundle_id).first()
            bundle.name = update_data['name']
            bundle.bags = update_data['bags']
            bundle.date = update_data['date']
            if 'vendor' in form and form['vendor']:
                bundle.vendor = Vendor.query.get(int(form['vendor']))
            pgdb.session.commit()

            if 'vendor' in form and form['vendor']:
                LOGGER.info(
                    event='edit_bundle_vendor',
                    order_id=str(bundle.str_id),
                    vendor_id=bundle.vendor.id if bundle.vendor is not None else None,
                    bundle_id=bundle.id
                )
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error.'}, 500

        return {'status': 'success'}


class Bundles(Resource):
    def _items_count(self, order_items):
        ret_count = {
            'laundry': 0,
            'dryclean': 0,
            'iron': 0
        }
        for item in order_items:
            if 'quantity' not in item:
                continue
            ret_count['laundry'] += item['quantity'].get('laundry', 0)
            ret_count['iron'] += item['quantity'].get('iron', 0)
            ret_count['dryclean'] += item['quantity'].get('dryclean', 0)

        return ret_count

    def _last_modified_dates(self, bundle_ids):
        # Get last modified dates
        last_modified_map = {}
        try:
            last_modifieds = log_db.general_logs.find({'event': 'edit_bundle_vendor', 'bundle_id': {'$in': bundle_ids}})
            for last_modified in last_modifieds:
                if last_modified['bundle_id'] not in last_modified_map:
                    last_modified_map[last_modified['bundle_id']] = last_modified['timestamp']
                else:
                    if last_modified['timestamp'] > last_modified_map[last_modified['bundle_id']]:
                        last_modified_map[last_modified['bundle_id']] = last_modified['timestamp']
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500
        return last_modified_map

    def get(self, datestamp):
        if not datestamp:
            return {'status': 'failure', 'error': 'Date not provided.'}, 403

        try:
            datestamp = datetime.strptime(datestamp, "%Y-%m-%d")
        except Exception:
            return {'status': 'failure', 'error': 'Date not in proper format.'}, 403
        
        bundle_dict = {}
        try:
            bundles = TagBundle.query.filter(TagBundle.date == datestamp)
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        bundle_ids = []
        for bundle in bundles:
            bundle_ids.append(bundle.id)
            for bag in bundle.bags:
                bundle_dict[str(bag)] = bundle.id

        last_modified_dates = self._last_modified_dates(bundle_ids)

        pickup_list = []
        try:
            schedules = list(db.schedules.find({
                'is_pickup': True,
                'schedule_date': datestamp.strftime('%Y/%m/%d')
            }, {'_id': 1}))
            for schedule in schedules:
                pickup_list.append(schedule['_id'])
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        bundle_list = bundle_dict.keys()

        try:
            orders = db.orders.find(
                {
                    'pickup_id': {'$in': pickup_list},
                    '$or': [
                        {'bag.laundry': {'$in': bundle_list}},
                        {'bag.dryclean': {'$in': bundle_list}},
                        {'bag.iron': {'$in': bundle_list}}
                    ]
                },
                {'order_id': 1, 'bag': 1, 'pickup_id': 1, 'order_items': 1}
            )
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        schedule_list = []
        for order in orders:
            schedule_list.append(str(order['pickup_id']))

        orders.rewind()
        
        bundle_order_dict = {}
        bundle_contents = {}
        for order in orders:
            if str(order['pickup_id']) not in schedule_list:
                continue
            if 'bag' in order:
                for service_type, bags in order['bag'].iteritems():
                    for bag in bags:
                        if bag not in bundle_dict:
                            continue
                        if bundle_dict[bag] not in bundle_order_dict:
                            bundle_order_dict[bundle_dict[bag]] = []
                            bundle_contents[bundle_dict[bag]] = {}
                        
                        if order['order_id'] not in bundle_order_dict[bundle_dict[bag]]:
                            bundle_order_dict[bundle_dict[bag]].append(order['order_id'])
                        
                        if order['order_id'] not in bundle_contents[bundle_dict[bag]]:
                            bundle_contents[bundle_dict[bag]][order['order_id']] = {}

                        if service_type not in bundle_contents[bundle_dict[bag]][order['order_id']]:
                            bundle_contents[bundle_dict[bag]][order['order_id']] = {
                                'bags': {
                                    service_type: [bag]
                                },
                                'quantity': {
                                    service_type: self._items_count(order['order_items'])[service_type]
                                }
                            }
                        else:
                            bundle_contents[bundle_dict[bag]][order['order_id']]['bags'][service_type].append(bag)
        
        for content in bundle_contents.itervalues():
            total_quantity = 0
            for actual_content in content.values():
                total_quantity += actual_content['quantity'].get('laundry', 0) + actual_content['quantity'].get('iron', 0) + actual_content['quantity'].get('dryclean', 0)
            content['total_quantity'] = total_quantity

        result = {}
        for bundle in bundles:
            item = {}
            item['vendor_last_modified'] = last_modified_dates[bundle.id] if bundle.id in last_modified_dates else None
            if bundle.id in bundle_contents:
                item['contents'] = bundle_contents[bundle.id]
                item['total_quantity'] = item['contents']['total_quantity']
                item['contents'].pop('total_quantity')
            else:
                item['contents'] = {}
                item['total_quantity'] = 0
            item['order_id'] = bundle_order_dict[bundle.id] if bundle.id in bundle_order_dict else None
            item['name'] = bundle.name
            item['date'] = bundle.date.strftime("%Y-%m-%d")
            item['vendor'] = bundle.vendor.data['name'] if bundle.vendor else None
            item['bags'] = bundle.bags
            # item.pop('id')
            # item.pop('str_id')
            result[bundle.str_id] = item
        return jsonify({'data': result})
