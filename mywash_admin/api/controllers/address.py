from flask.ext.restful import Resource
from flask import jsonify, request
import datetime
from mywash_admin import app
import copy
import bson
import json
from api.models import OperationalCity, MywashHub
import re
from mywash_admin.lib.loggers import MongoLogger

db = app.config['MONGO_CLIENT']['dealsup']

gmaps = app.config['GOOGLE_MAPS']

EXCEPTION_LOGGER = MongoLogger('mywash_logs', 'exception_logs')


class Address(Resource):
    def base_address(self):
        return {
            "user_id": "",
            "address_1": "SFS 407, Yelahanka New Town,",
            "tag": "",
            "address_2": "SFS 407, Yelahanka New Town,",
            "state": "karnataka",
            "city": "bangalore",
            "apartment_number": "",
            "pincode": 0,
            "is_active": True,
            'locality': {
                'map_string': '',
                'lat': None,
                'lng': None
            },
            'assigned_hub': None
        }

    def _get_nearest_hub(self, locality):
        # For now city default to Bengaluru i.e. 1
        city = OperationalCity.query.get(1)
        min_distance = None
        selected_hub = None

        for hub in city.mywashhub:
            data = copy.deepcopy(hub.data)
            result = gmaps.distance_matrix(
                origins=(locality['lat'], locality['lng']),
                destinations=(data['coord']['lat'], data['coord']['lng'])
            )
            try:
                result = result['rows'][0]['elements'][0]['distance']['value']
            except Exception, e:
                EXCEPTION_LOGGER.error(
                    "gmaps distance matrix error",
                    event='gmaps_distance_compute',
                    locality=locality,
                    hub=data,
                    result=result
                )
                return False
            if min_distance is None or min_distance > result:
                min_distance = result
                selected_hub = hub
        return selected_hub

    def get(self, address_id=None):
        addresses = None
        try:
            if address_id:
                addresses = db.addresses.find({
                    '_id': bson.ObjectId(address_id)})
            else:
                addresses = db.addresses.find()
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500
        json_docs = []
        hub_list = set()
        for address in addresses:
            result = copy.deepcopy(address)
            for k, v in address.items():
                if isinstance(v, bson.ObjectId):
                    result[k] = str(v)
            if 'assigned_hub' in address:
                hub_list.add(address['assigned_hub'])
            json_docs.append(result)
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

        for doc in json_docs:
            if 'assigned_hub' in doc:
                doc['assigned_hub'] = hubs_dict[doc['assigned_hub']]

        return jsonify({"data": json_docs})

    def post(self):
        schema = self.base_address()
        form = copy.deepcopy(request.form)
        print form
        if 'address_1' not in form and not form['address_1']:
            return {'status': 'failure', 'error': 'Address not provided.'}, 403
        if 'address_2' not in form and not form['address_2']:
            return {'status': 'failure', 'error': 'Landmark not provided.'}, 403
        if 'user_id' not in form and not form['user_id']:
            return {'status': 'failure', 'error': 'User id not provided.'}, 403
        if 'tag' not in form and not form['tag']:
            return {'status': 'failure', 'error': 'Tag not provided.'}, 403
        elif db.addresses.find({
            'user_id': form['user_id'],
            'tag': re.compile('^' + form['tag'] + '$', re.IGNORECASE),
            'is_active': True
        }).count():
            return {'status': 'failure', 'error': 'Tag already exists.'}, 403
        if 'locality' not in form and not form['locality']:
            return {'status': 'failure', 'error': 'Locality not provided.'}, 403
        locality = json.loads(form['locality'])
        if not ('map_string' in locality and 'lat' in locality and 'lng' in locality):
            return {'status': 'failure', 'error': 'Locality not in proper format.'}, 403
        # For now city default to Bengaluru
        # locality['city'] = 1
        try:
            tag = form.get("tag") if form.get("tag") != "" else form.get("address_1")[:4]
        except Exception, e:
            print str(e)
            tag = "Default"
        schema["tag"] = tag
        schema['locality'] = locality
        schema["is_active"] = True
        schema["pincode"] = form.get("pincode")
        nearest_hub = self._get_nearest_hub(locality)
        if not nearest_hub:
            return {'status': 'failure', 'error': 'Error getting distance.'}, 403
        schema['assigned_hub'] = nearest_hub.id
        schema["address_1"] = form.get("address_1")
        schema["address_2"] = form.get("address_2")
        schema["apartment_number"] = form.get("apartment_number", None)
        schema["user_id"] = form.get("user_id")
        schema['update_time'] = datetime.datetime.utcnow()
        if 'partner_id' in form:
            schema['partner_id'] = form.get('partner_id')
        try:
            address_id = db.addresses.insert(schema)
        except Exception, e:
            return {'status': 'failure', 'error': 'db error'}, 500
        return {
            'status': 'success',
            'address_id': str(address_id),
            'assigned_hub': {
                'name': nearest_hub.data['name'],
                'short': nearest_hub.data['short'],
            }
        }

    def put(self, address_id):
        form = copy.deepcopy(request.form)
        address_data = {}
        nearest_hub = None
        if 'tag' in form:
            address_data['tag'] = form['tag']
        if 'apartment_number' in form:
            address_data['apartment_number'] = form['apartment_number']
        if 'address_1' in form:
            address_data['address_1'] = form['address_1']
        if 'address_2' in form:
            address_data['address_2'] = form['address_2']
        if 'locality' in form:
            address_data['locality'] = json.loads(form['locality'])
            nearest_hub = self._get_nearest_hub(address_data['locality'])
            if not nearest_hub:
                return {'status': 'failure', 'error': 'Error getting distance.'}, 403
            address_data['assigned_hub'] = nearest_hub.id
        if 'assigned_hub' in form:
            try:
                hub = MywashHub.query.filter(MywashHub.str_id == form[
                    'assigned_hub']).first()
                address_data['assigned_hub'] = hub.id
                nearest_hub = hub
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500
        if 'is_active' in form:
            if form['is_active'] == 'true':
                address_data['is_active'] = True
            elif form['is_active'] == 'false':
                address_data['is_active'] = False
            else:
                return {'status': 'failure', 'error': 'is_active has wrong parameter.'}
        if 'refresh_hub' in form and form['refresh_hub'] == 'true':
            try:
                address = db.addresses.find_one({'_id': bson.ObjectId(address_id)})
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'refresh hub db error'}, 500
            nearest_hub = self._get_nearest_hub(address['locality'])
            if not nearest_hub:
                return {'status': 'failure', 'error': 'Error getting distance.'}, 403
            address_data['assigned_hub'] = nearest_hub.id
        if len(address_data):
            address_data['update_time'] = datetime.datetime.utcnow()
        if address_data:
            try:
                db.addresses.update(
                    {'_id': bson.ObjectId(address_id)},
                    {'$set': address_data}
                )
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error'}, 500
            if nearest_hub is not None:
                address_data['assigned_hub'] = {
                    'str_id': nearest_hub.str_id,
                    'name': nearest_hub.data['name'],
                    'short': nearest_hub.data['short'],
                }
            return jsonify({'status': 'success', 'update_data': address_data})
        return {'status': 'success'}

    def delete(self, address_id):
        try:
            address_count = db.addresses.find_one({
                '_id': bson.ObjectId(address_id)})
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 403
        if not address_count:
            return {'status': 'failure', 'error': 'Address does not exist'}, 403
        try:
            db.addresses.update({'_id': bson.ObjectId(address_id)}, {'$set': {
                'is_active': False}})
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 403
        return {'status': 'success'}


class UserAddress(Resource):
    def get(self, user_id=None):
        addresses = None
        try:
            if user_id:
                addresses = db.addresses.find({'user_id': user_id,
                 'is_active': True})
            else:
                addresses = db.addresses.find()
            
        except Exception, e:
            return {'status': 'failure', 'error': 'db error'}
        
        json_docs = []
        hub_list = set()
        for address in addresses:
            result = copy.deepcopy(address)
            for k, v in address.items():
                if isinstance(v, bson.ObjectId):
                    result[k] = str(v)
            if 'assigned_hub' in address:
                hub_list.add(address['assigned_hub'])
            json_docs.append(result)
        
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

        for doc in json_docs:
            if 'assigned_hub' in doc:
                doc['assigned_hub'] = hubs_dict[doc['assigned_hub']]

        return jsonify({"data": json_docs})

