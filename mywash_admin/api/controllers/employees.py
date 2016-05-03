from flask.ext.restful import Resource
from flask import jsonify, request, session
from datetime import datetime
from mywash_admin import app, db as pgdb
import json
import copy
from api.models import Employee as EmployeeModel, MywashHub
from mywash_admin.lib.loggers import MongoLogger
import requests
from sqlalchemy import and_

db = app.config['MONGO_CLIENT']['dealsup']

EXCEPTION_LOGGER = MongoLogger('mywash_logs', 'exception_logs')


class Employee(Resource):
    def _schema(self):
        return {
            'name': None,
            'phone': None,
            'is_active': True,
            'shift': None,
        }

    def get(self, **kwargs):
        emp_id = None
        skip = 0
        limit = 20

        if 'emp_id' in kwargs:
            emp_id = kwargs['emp_id']

        if 'skip' in kwargs:
            skip = kwargs['skip']

        if 'limit' in kwargs:
            limit = kwargs['limit']

        if limit > 100:
            limit = 20

        try:
            if emp_id:
                staffs = EmployeeModel.query.filter(EmployeeModel.str_id == emp_id).first()
            else:
                staffs = EmployeeModel.query.filter(EmployeeModel.is_active == True).order_by(EmployeeModel.id.desc())
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error.'}, 500

        result = []
        if isinstance(staffs, EmployeeModel):
            item = {}
            item['str_id'] = staffs.str_id
            item['data'] = staffs.data
            item['notification'] = staffs.notification
            if staffs.mywashhub:
                item['hub'] = {
                    'name': staffs.mywashhub.data['name'],
                    'short': staffs.mywashhub.data['short'],
                    'str_id': staffs.mywashhub.str_id,
                }
                item['emp_id'] = "%s%d" % (staffs.mywashhub.data['short'], staffs.id)
            else:
                item['emp_id'] = "%d" % staffs.id
            item['is_active'] = staffs.is_active
            result.append(item)
        else:
            for staff in staffs:
                item = {}
                item['str_id'] = staff.str_id
                item['data'] = staff.data
                item['notification'] = staff.notification
                if staff.mywashhub:
                    item['hub'] = {
                        'name': staff.mywashhub.data['name'],
                        'short': staff.mywashhub.data['short'],
                        'str_id': staff.mywashhub.str_id,
                    }
                    item['emp_id'] = "%s%d" % (staff.mywashhub.data['short'], staff.id)
                else:
                    item['emp_id'] = "%d" % staff.id
                item['is_active'] = staff.is_active
                result.append(item)
        return jsonify({'data': result})

    def post(self):
        form = copy.deepcopy(request.form)
        if 'name' not in form:
            return {'status': 'failure', 'error': 'Name not provided.'}, 403

        if 'phone' not in form:
            return {'status': 'failure', 'error': 'Phone number not provided.'}, 403

        if 'shift' not in form:
            return {'status': 'failure', 'error': 'Shift not provided.'}, 403
        elif not (form['shift'] == "1" or form['shift'] == "2"):
            return {'status': 'failure', 'error': 'Shift value incorrect.'}, 403

        if 'hub_id' not in form:
            return {'status': 'failure', 'error': 'Status not provided.'}, 403

        schema = self._schema()
        schema['name'] = form['name']
        schema['shift'] = form['shift']
        schema['phone'] = json.loads(form['phone'])
        hub_id = form['hub_id']
        
        try:
            employee = EmployeeModel(data=schema)
            hub = MywashHub.query.filter(MywashHub.str_id == hub_id).first()
            employee.hub_id = hub.id
            if 'is_active' in form:
                if form['is_active'] == "true":
                    employee.is_active = True
                elif form['is_active'] == "false":
                    employee.is_active = False
            pgdb.session.add(employee)
            pgdb.session.commit()
            return {'status': 'success', 'str_id': employee.str_id, 'emp_id': "%.5d" % employee.id}
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error.'}, 500

    def put(self, emp_id):
        form = copy.deepcopy(request.form)

        employee = None
        try:
            employee = EmployeeModel.query.filter(EmployeeModel.str_id==emp_id).first()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        data = copy.deepcopy(employee.data)
        if 'name' in form and form['name']:
            data['name'] = form['name']

        if 'phone' in form and form['phone']:
            data['phone'] = json.loads(form['phone'])

        if 'shift' in form and form['shift']:
            if form['shift'] == "1" or form['shift'] == "2":
                data['shift'] = form['shift']

        if 'is_active' in form and form['is_active']:
            if form['is_active'] == "true":
                employee.is_active = True
            elif form['is_active'] == "false":
                employee.is_active = False

        if 'hub_id' in form and form['hub_id']:
            emp = MywashHub.query.filter(MywashHub.str_id == form['hub_id']).first()
            employee.hub_id = emp.id

        employee.data = data
        employee.last_modified = datetime.utcnow()
        try:
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        return {'status': 'success'}


class EmployeeSearch(Resource):
    def get(self, **kwargs):
        skip = 0
        limit = 10

        if not kwargs['term']:
            return {'status': 'failure', 'error': "no search term provided."}, 403

        term = kwargs['term'].strip()

        # try:
        employees = EmployeeModel.query.filter(
            (EmployeeModel.data['name'].startswith(term)) &
            (EmployeeModel.data['is_active'] == 'true')
        )
        result = []
        for employee in employees:
            item = {}
            item['name'] = employee.data['name']
            item['phone'] = employee.data['phone']
            item['emp_id'] = "%.5d" % employee.id
            item['str_id'] = employee.str_id
            result.append(item)
        return result


class EmployeeVerification(Resource):
    def get(self, emp_phone):
        if len(emp_phone) < 10 or len(emp_phone) > 13:
            return {'status': 'failure', 'error': "no invalid phone number."}, 403
        emp = None
        try:
            print '{"phone":["%s"]}' % emp_phone
            emp = EmployeeModel.query.filter(
                    EmployeeModel.data.contains(
                        '{"phone": ["%s"]}' % emp_phone
                    ) & (EmployeeModel.is_active == True)
                )
            if emp.count():
                result = {}
                result['str_id'] = emp[0].str_id
                result['name'] = emp[0].data['name']
                result['phone'] = emp[0].data['phone'][0]
                result['shift'] = emp[0].data['shift']
                result['is_active'] = emp[0].is_active
                result['hub'] = 'MRT' if emp[0].hub_id == 2 else 'ANY'
                result['emp_id'] = result['hub'] + str(emp[0].id)
                return {'status': 'success', 'data': result}
            else:
                return {'status': 'failure', 'error': "Unauthorized Number!\nPlease Contact Your Manager."}, 404
        except Exception as e:
            return {'status': 'failure', 'error': "db error"}, 403

    def post(self):
        form = copy.deepcopy(request.form)
        emp_phone = form['emp_phone'] if 'emp_phone' in form else ''
        installation_id = form['installation_id'] if 'installation_id' in form else ''
        if len(emp_phone) < 10 or len(emp_phone) > 13:
            return {'status': 'failure', 'error': "no invalid phone number."}, 403
        if not installation_id:
            return {'status': 'failure', 'error': "failed to get installation id"}, 403

        emp = None
        try:
            emps = EmployeeModel.query.filter(
                EmployeeModel.notification.contains({"installation_id": installation_id})
            )

            for emp in emps:
                notification = copy.deepcopy(emp.notification)
                notification['installation_id'] = ""
                emp.notification = notification
                emp.last_modified = datetime.utcnow()
                pgdb.session.add(emp)
                pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        try:
            emp = EmployeeModel.query.filter(
                    EmployeeModel.data.contains(
                        '{"phone": ["%s"]}' % emp_phone
                    ) & (EmployeeModel.is_active == True)
                ).first()
            if not emp:
                return {'status': 'failure', 'error': "Unauthorized Number!\nPlease Contact Your Manager."}, 404

            notification = None
            if emp.notification:
                notification = copy.deepcopy(emp.notification)
            else:
                notification = {}
                notification['name'] = 'parse'
            notification['installation_id'] = installation_id
            emp.notification = notification
            emp.last_modified = datetime.utcnow()
            pgdb.session.commit()
        except Exception, e:
            return {'status': 'failure', 'error': 'db error.'}, 500

        if (emp is not None):
            result = {}
            result['str_id'] = emp.str_id
            result['name'] = emp.data['name']
            result['phone'] = emp.data['phone'][0]
            result['shift'] = emp.data['shift']
            result['is_active'] = emp.is_active
            result['hub'] = 'MRT' if emp.hub_id == 2 else 'ANY'
            result['emp_id'] = result['hub'] + str(emp.id)
            return {'status': 'success', 'data': result}
        else:
            return {'status': 'failure', 'error': "Unauthorized Number!\nPlease Contact Your Manager."}, 404


class EmployeeLogin(Resource):
    def post(self):
        form = copy.deepcopy(request.form)
        payload = {"access_token": form['code']}
        response = requests.get("https://www.googleapis.com/plus/v1/people/me", params=payload).json()

        if 'mywash.com' not in response['emails'][0]['value']:
            return {'status': 'failure', 'error': 'invalid user'}, 403
        
        emp_data = {
            'name': response['displayName'],
            'email': response['emails'][0]['value'],
            'gender': response['gender'],
            'id': response['id'],
            'profile': response['url']
        }

        try:
            employee = EmployeeModel.query.filter(
                EmployeeModel.login_creds.contains(
                    {'email': emp_data['email']}
                ) & EmployeeModel.is_active == True
            ).first()
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error'}, 500

        if employee:
            session['employee_registered'] = True
        else:
            session['employee_registered'] = False

        session['login_status'] = True
        session['emp_data'] = emp_data

        return {'status': 'success'}
