from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
from mywash_admin import db as pgdb
from api.models import MywashHub


class Hub(Resource):
    def get(self, **kwargs):
        hub_id = None
        if 'hub_id' in kwargs:
            hub_id = kwargs['hub_id']

        if hub_id:
            try:
                hub_data = MywashHub.query.get(hub_id)
                return {'data': [hub_data]}
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}
        else:
            try:
                hubs = list(MywashHub.query.all())
                result = []
                for hub in hubs:
                    item = hub.data
                    item['str_id'] = hub.str_id
                    result.append(item)
                return {'data': result}
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}
    
    def post(self):
        pass