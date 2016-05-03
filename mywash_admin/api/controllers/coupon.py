from flask.ext.restful import Resource
from flask import jsonify, request
import bson
from datetime import datetime
import copy
from api.models import UserOrderCoupon as UOCModel
from api.models import Coupon as CouponModel
from mywash_admin import app, db as pgdb
from mywash_admin import settings
import json
from sqlalchemy import and_
import importlib

db = app.config['MONGO_CLIENT']['dealsup']

redis_client = app.config['REDIS_CLIENT']


class Coupon(Resource):
    def _schema(self):
        return {
            'name': None,
            'data': None,
            'alias_coupon': None,
            'start_date': None,
            'expiry_date': None,
            'is_active': True,
        }

    def post(self):
        form = copy.deepcopy(request.form)
        if 'name' not in form:
            return {'status': 'failure', 'error': 'Name not provided.'}, 403

        if 'data' not in form:
            return {'status': 'failure', 'error': 'Data not provided.'}, 403

        if 'alias_coupon' not in form:
            return {'status': 'failure', 'error': 'Alias coupon not provided.'}, 403

        if 'start_date' not in form:
            return {'status': 'failure', 'error': 'Start date not provided.'}, 403

        if 'expiry_date' not in form:
            return {'status': 'failure', 'error': 'Expiry date not provided.'}, 403

        if 'is_active' not in form:
            return {'status': 'failure', 'error': 'Status not provided.'}, 403

        schema = self._schema()
        schema['name'] = form['name']
        schema['data'] = form['data']
        schema['alias_coupon'] = form['alias_coupon']
        schema['start_date'] = form['start_date']
        schema['expiry_date'] = form['expiry_date']
        schema['is_active'] = form['is_active']

        try:
            coupon = CouponModel(data=schema)
            if 'is_active' in form:
                if form['is_active'] == "true":
                    coupon.is_active = True
                elif form['is_active'] == "false":
                    coupon.is_active = False
            pgdb.session.add(coupon)
            pgdb.session.commit()
            return {'status': 'success', 'str_id': coupon.str_id, 'coupon_id': "%.5d" % coupon.id}
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error.'}, 500

    def put(self, coup_id):
        form = copy.deepcopy(request.form)

        coupon = None
        try:
            coupon = CouponModel.query.filter(CouponModel.str_id == coup_id).first()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        data = copy.deepcopy(coupon.data)
        if 'name' in form and form['name']:
            data['name'] = form['name']

        if 'max' in form and form['max']:
            data['max'] = form['max']

        if 'count' in form and form['count']:
            data['count'] = form['count']

        if 'amount' in form and form['amount']:
            data['amount'] = form['amount']

        if 'percentage' in form and form['percentage']:
            data['percentage'] = form['percentage']

        if 'is_active' in form and form['is_active']:
            if form['is_active'] == "true":
                coupon.is_active = True
            elif form['is_active'] == "false":
                coupon.is_active = False

        if 'start_date' in form and form['start_date']:
            coupon.start_date = form['start_date']

        if 'expiry_date' in form and form['expiry_date']:
            coupon.expiry_date = form['expiry_date']

        coupon.data = data
        coupon.last_modified = datetime.utcnow()
        try:
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        return {'status': 'success'}
    
    def get(self, **kwargs):
        if 'name' in kwargs:
            name = kwargs['name']

            print "coupon name get..",name,"......."
            try:
                coupon_data = CouponModel.query.filter(
                    CouponModel.data['name'].astext == name.lower()
                ).first()
            except Exception, e:
                return {'status': 'failure', 'error': 'db error.'}, 500
            
            if coupon_data:
                result = {'status': 'success'}
                result.update({'str_id': coupon_data.str_id})
                if coupon_data.data['amount']:
                    result.update({'amount': coupon_data.data['amount']})
                if coupon_data.data['name']:
                    result.update({'name': coupon_data.data['name']})
                if coupon_data.data['max']:
                    result.update({'max': coupon_data.data['max']})
                if coupon_data.data['percentage']:
                    result.update({'percentage': coupon_data.data['percentage']})
                if coupon_data.data['min_order']:
                    result.update({'min_order': coupon_data.data['min_order']})
                if coupon_data.data['terms']:
                    result.update({'terms': coupon_data.data['terms']})
            else:
                result = {'status': 'failure', 'error': "coupon not available."}, 403
            return result
        else:
            coup_id = None
            skip = 0
            limit = 20

            if 'coup_id' in kwargs:
                coup_id = kwargs['coup_id']

            if 'skip' in kwargs:
                skip = kwargs['skip']

            if 'limit' in kwargs:
                limit = kwargs['limit']

            if limit > 100:
                limit = 20

            coupons = None
            try:
                if coup_id:
                    coupons = CouponModel.query.filter(CouponModel.str_id == coup_id).first()
                else:
                    coupons = CouponModel.query.filter(
                        CouponModel.is_active == True).order_by(CouponModel.id.desc())
            except Exception, e:
                print e
                return {'status': 'failure', 'error': 'db error.'}, 500

            result = []
            if isinstance(coupons, CouponModel):
                item = {}
                item['str_id'] = coupons.str_id
                item['data'] = coupons.data
                item['alias_coupon'] = coupons.alias_coupon
                item['start_date'] = coupons.start_date
                item['expiry_date'] = coupons.expiry_date
                item['is_active'] = coupons.is_active
                result.append(item)
            else:
                item = {}
                for coupon in coupons:
                    item = {}
                    item['str_id'] = coupon.str_id
                    item['data'] = coupon.data
                    item['alias_coupon'] = coupon.alias_coupon
                    item['start_date'] = coupon.start_date
                    item['expiry_date'] = coupon.expiry_date
                    item['is_active'] = coupon.is_active
                    result.append(item)
            return {'data': result}


class CouponVerification(Resource):
    def get(self, **kwargs):
        if 'order_id' in kwargs and kwargs['order_id']:
            order_id = kwargs['order_id']
            try:
                uoc = UOCModel.query.filter(UOCModel.order == order_id).first()
            except Exception, e:
                return {'status': 'failure', 'error': "db error"}, 500
            if uoc:
                try:
                    coupon_data = CouponModel.query.filter(CouponModel.str_id == uoc.coupon).first()
                except Exception, e:
                    return {'status': 'failure', 'error': "db error"}, 500
                return {'status': 'success', 'name': coupon_data.data['name']}
            else:
                return {'status': 'failure', 'error': "Coupon doesn't exist."}, 403
        elif 'uoc_id' in kwargs and kwargs['uoc_id']:
            uoc_id = kwargs['uoc_id']
            uoc = UOCModel.query.filter(UOCModel.str_id == uoc_id).first()
            if uoc:
                coupon_data = CouponModel.query.filter(CouponModel.str_id == uoc.coupon).first()
                return {'status': 'success', 'service': coupon_data.service}
            else:
                return {'status': 'failure', 'error': "Coupon doesn't exist."}, 403
        return {'status': 'failure', 'error': ""}, 403

    def post(self, coupon=None):
        if coupon == 'coupon':
            form = copy.deepcopy(request.form)
            u_id = ""
            coupon_name = ""
            service = ""

            if 'coupon' in form and form['coupon']:
                coupon_name = form['coupon']
            if 'user_id' in form and form['user_id']:
                u_id = form['user_id']
            if 'service' in form and form['service']:
                service = form['service']
            verification_message = {}
            if not coupon_name.strip():
                return {'status': "success", 'message': 'No Coupon Applied.'}

            coupon_data = CouponModel.query.filter(
                CouponModel.data['name'].astext == coupon_name.strip().lower()
            ).first()

            # code for importing the class of coupon and verifying it
            if coupon_data and coupon_data.str_id:
                try:
                    user_id = str(db.users.find_one({"user_id": u_id})["_id"])
                    coupon_file = importlib.import_module("api.coupons.%s" % coupon_data.str_id)
                    coupon = coupon_file.Coupon(coupon_data.str_id, service, user_id)
                    verification_message = coupon.validate()
                except ImportError, e:
                    # Display error messag
                    print e
                    return {"status": 'failure', "error": "Unexpected Error: Coupon Validity unknown."}, 500

                try:
                    if verification_message['status'] == "success":
                        if 'amount' in coupon_data.data:
                            verification_message["amount"] = coupon_data.data["amount"]
                        if 'min_order' in coupon_data.data:
                            verification_message["min_order"] = coupon_data.data["min_order"]
                        if 'name' in coupon_data.data:
                            verification_message["name"] = coupon_data.data['name']
                        if coupon_data.str_id:
                            verification_message["str_id"] = coupon_data.str_id
                        if 'terms' in coupon_data.data:
                            verification_message["terms"] = coupon_data.data["terms"]
                        verification_message['status'] = "success"
                        return verification_message
                    else:
                        if verification_message['error'] == 'db':
                            return verification_message, 500
                        else:
                            return verification_message, 403

                except Exception, e:
                    return {'status': 'failure', 'error': 'db error'}, 500

                return verification_message
            else:
                return {'status': 'failure', 'error': 'The coupon code entered by you is invalid. Please enter a valid code.'}, 403
        else:
            form = copy.deepcopy(request.form)
            ### this field user_id, coupon must be added on phone forms
            u_id = ""
            coupon_name = ""
            service = ""

            if 'coupon' in form and form['coupon']:
                coupon_name = form['coupon']
            if 'user_id' in form and form['user_id']:
                u_id = form['user_id']
            if 'service' in form and form['service']:
                service = form['service']

            if not coupon_name.strip():
                return {'status': "success", 'message': 'No Coupon Applied'}

            coupon_data = CouponModel.query.filter(
                CouponModel.data['name'].astext == coupon_name.strip().lower()
            ).first()
            verification_message = {}
            # code for importing the class of coupon and verifying it
            if coupon_data and coupon_data.str_id:
                try:
                    user_id = str(db.users.find_one({"user_id": u_id})["_id"])
                    coupon_file = importlib.import_module("api.coupons.%s" % coupon_data.str_id)
                    coupon = coupon_file.Coupon(coupon_data.str_id, service, user_id)
                    verification_message = coupon.validate()
                except ImportError, e:
                    # Display error messag
                    print e
                
                try:
                    if verification_message['status'] == "success":
                        user_order_coupon = UOCModel()
                        user_order_coupon.user = user_id
                        user_order_coupon.coupon = str(coupon_data.str_id)
                        #we are ignoring adding order, which will be added while submitting the order
                        pgdb.session.add(user_order_coupon)
                        pgdb.session.commit()

                        verification_message['uoc_id'] = user_order_coupon.str_id
                        verification_message['status'] = "success"
                    else:
                        if verification_message['error'] == 'db':
                            return verification_message, 500
                        else:
                            return verification_message, 403

                except Exception, e:
                    return {'status': 'failure', 'error': 'db error'}, 500

                return verification_message
            else:
                return {'status': 'failure', 'error': 'The coupon code entered by you is invalid. Please enter a valid code.'}, 403

    def put(self):
        form = copy.deepcopy(request.form)
        if 'method' in form:
            if form['method'] == 'update':
                if form['uoc_str_id']:
                    if not form['uoc_str_id'] == 'undefined':
                        return self.__update(form)
            elif form['method'] == 'delete':
                return self.__delete(form)

        return {'status': 'failure'}

    #can be extended with other ids as well, in this case only based on order
    def __delete(self, formdata):
        uoc = UOCModel.query.filter(UOCModel.order == formdata['order']).first()
        pgdb.session.delete(uoc)
        pgdb.session.commit()
        return {'status': 'success'}

    def __update(self, formdata):
        row = UOCModel.query.filter(UOCModel.str_id == formdata['uoc_str_id']).first()
        row.order = formdata['order']
        pgdb.session.commit()
        return {'status': 'success'}
