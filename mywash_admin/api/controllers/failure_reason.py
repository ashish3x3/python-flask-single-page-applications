from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from mywash_admin import app
import copy
import bson
import json
from api.models import Reason
from sqlalchemy import Boolean, or_
from mywash_admin import db as pgdb


class FailureReason(Resource):
    def get(self, **kwargs):
        reason_type = kwargs['reason_type'] if 'reason_type' in kwargs else None
        reason_id = kwargs['reason_id'] if 'reason_id' in kwargs else None
        
        reasons = None
        try:
            if reason_type:
                reasons = Reason.query.filter(Reason.data[reason_type].cast(Boolean)==True)
            elif reason_id:
                reasons = Reason.query.filter(Reason.str_id == reason_id)
            else:
                reasons = Reason.query.filter(or_(
                    Reason.data['pickup'].cast(Boolean) == True,
                    Reason.data['delivery'].cast(Boolean) == True,
                    Reason.data['partial_payment'].cast(Boolean) == True
                ))
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        result = []
        for reason in reasons:
            reason_types = []
            if 'pickup' in reason.data:
                reason_types.append({'name': 'pickup', 'formal_name': 'Pickup'})
            if 'delivery' in reason.data:
                reason_types.append({'name': 'delivery', 'formal_name': 'Delivery'})
            if 'partial_payment' in reason.data:
                reason_types.append({'name': 'partial_payment', 'formal_name': 'Partial payment'})

            result.append({'str_id': reason.str_id, 'reason': reason.data['reason'], 'type': reason_types})

        return {'data': result}

    def post(self):
        form = copy.deepcopy(request.form)
        data = {}
        if 'reason' in form:
            data['reason'] = form['reason']
        else:
            return {'status': 'failure', 'error': 'reason not provided.'}, 403

        if 'type' in form:
            try:
                types = json.loads(form['type'])
            except Exception, e:
                return {'status': 'failure', 'error': 'invalid json format.'}, 403
            
            if 'pickup' in types:
                data['pickup'] = True

            if 'delivery' in types:
                data['delivery'] = True

            if 'partial_payment' in types:
                data['partial_payment'] = True
        else:
            return {'status': 'failure', 'error': 'type not provided.'}, 403

        try:
            reason = Reason()
            reason.data = data
            pgdb.session.add(reason)
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        return {'status': 'success', 'str_id': reason.str_id}

    def put(self, reason_id):
        form = copy.deepcopy(request.form)
        try:
            reason = Reason.query.filter(Reason.str_id == reason_id).first()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500
         
        data = copy.deepcopy(reason.data)
        update_data = {}
        if 'reason' in form:
            update_data['reason'] = form['reason']
        else:
            update_data['reason'] = data['reason']

        if 'type' in form:
            try:
                types = json.loads(form['type'])
            except Exception, e:
                return {'status': 'failure', 'error': 'invalid json format.'}, 403
            
            if 'pickup' in types:
                update_data['pickup'] = True

            if 'delivery' in types:
                update_data['delivery'] = True

            if 'partial_payment' in types:
                update_data['partial_payment'] = True

        try:
            reason.data = update_data
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        return {'status': 'success'}


