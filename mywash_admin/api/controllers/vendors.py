from flask.ext.restful import Resource
from flask import request
from datetime import datetime
from mywash_admin import app, db as pgdb
import copy
from api.models import ServiceType, Vendor
import json


class Vendors(Resource):
    SERVICE_TYPES = {str(service.id): service for service in ServiceType.query.all()}

    def get(self, arg=None, limit=20):
        skip = 0
        vendor_id = None
        if isinstance(arg, int):
            skip = arg
        else:
            vendor_id = arg
        vendors = None
    
        if not vendor_id:
            try:
                vendors = Vendor.query.offset(skip).limit(limit)
            except Exception, e:
                print e
                return {'status': 'failure', 'error': "db error."}, 500
            
            result = {}
            for vendor in vendors:
                ############# N + 1 condition. Must be optimized with proper joins. #############
                services = vendor.services
                item = {
                    'str_id': vendor.str_id,
                    'data': vendor.data,
                    'is_active': vendor.is_active,
                    'services': [service.name for service in services],
                    'joining_date': vendor.joining_date.strftime("%Y-%m-%d %H:%M:%s%Z")
                }
                result[vendor.str_id] = item
            return result
        else:
            try:
                vendor = Vendor.query.filter(Vendor.str_id == vendor_id).first()
            except Exception, e:
                print e
                return {'status': 'failure', 'error': "db error."}, 500
            
            services = vendor.services
            result = {
                'name': vendor.data['name'],
                'email': vendor.data['email'],
                'phone': vendor.data['phone'],
                'address': vendor.data['address'],
                'is_active': vendor.is_active,
                'services': [{'name': service.name, 'id': service.id} for service in services]
            }
            return result
    
    def post(self):
        form = copy.deepcopy(request.form)
        data = {
            'name': form['name'],
            'phone': json.loads(form['phone']),
            'email': json.loads(form['email']),
            'address': form['address'],
        }
        services = json.loads(form['services'])
        vendor = Vendor(
            data=data,
            joining_date=datetime.utcnow()
        )
        vendor.is_active = json.loads(form['is_active'])
        
        # try:
        for service in services:
            vendor.services.append(self.SERVICE_TYPES[service])
        try:
            pgdb.session.add(vendor)
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': "db error."}, 500

        return {'status': 'success', 'str_id': str(vendor.str_id)}

    def put(self, arg):
        if not arg:
            return {'status': 'failure', 'error': "Vendor id not provided."}, 403

        form = copy.deepcopy(request.form)
        vendor = None
        try:
            if isinstance(arg, int):
                vendor = Vendor.get(arg)
            else:
                vendor = Vendor.query.filter_by(str_id=arg).first()
        except Exception, e:
            return {'status': 'failure', 'error': "db error."}, 500
        
        services = json.loads(form['services'])
        
        vendor.services = list(ServiceType.query.filter(ServiceType.id.in_(tuple(services))))

        data = copy.deepcopy(vendor.data)
        data = {
            'name': form['name'],
            'phone': json.loads(form['phone']),
            'email': json.loads(form['email']),
            'address': form['address'],
        }
        
        vendor.data = data
        vendor.is_active = json.loads(form['is_active'])
        vendor.last_modified = datetime.utcnow()

        try:
            pgdb.session.merge(vendor)
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': "db error."}, 500
        
        return {'status': 'success'}


class VendorSearch(Resource):
    def get(self, **kwargs):
        term = kwargs.get('term', None)
        skip = kwargs.get('skip', 0)
        limit = kwargs.get('limit', 10)
        try:
            vendors = Vendor.query.offset(skip).limit(limit)
            result = []
            for vendor in vendors:
                result.append({
                    'name': vendor.data['name'],
                    'id': vendor.id
                })
            return result
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "db error."}, 500
