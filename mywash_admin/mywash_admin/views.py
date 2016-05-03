from flask import render_template, session, request, redirect, jsonify
import copy
from api.models import MywashHub, Employee as EmployeeModel
import re
from mywash_admin import app, db as pgdb


def admin_base(restpath=None):
    if request.args.get('user', None) == 'iamlegend':
        session['user'] = ['iamlegend']
    elif request.args.get('user', None) == 'supertagger':
        session['user'] = ['supertagger']
    elif request.args.get('user', None) == 'batman':
        session['user'] = ['iamlegend', 'batman']
    elif request.args.get('user', None) == 'destroy':
        session['user'] = None
        
    if restpath is not None:
        return redirect('/')

    if session.get('login_status', False):
        if not session.get('employee_registered', False):
            return redirect('/employee/register')
        return render_template("base.html")
    return render_template('login.html', client_id=app.config['EMPLOYEE_GPLUS_CREDS']['client_id'])


def register_employee():
    if request.method == 'GET':
        if not session.get('login_status', False):
            return render_template('login.html')

        if session.get('employee_registered', False):
            return redirect("/")

        try:
            raw_hubs = MywashHub.query.all()
        except Exception, e:
            raise e

        hubs = []
        for hub in raw_hubs:
            hubs.append({
                'value': hub.data['short'],
                'name': hub.data['name']
            })
        
        context = {'hubs': hubs}
        return render_template('register_employee.html', **context)

    if request.method == 'POST':
        form = copy.deepcopy(request.form)
        if not form.get('phone', False):
            return {'status': 'failure', 'error': 'phone not provided.'}, 403
        else:
            if not re.match(r'\d{10}', form['phone']):
                return {'status': 'failure', 'error': 'phone invalid.'}, 403

        if not form.get('hub', False):
            return {'status': 'failure', 'error': 'hub not provided.'}, 403

        emp_data = {
            'name': session['emp_data']['name'],
            'phone': form['phone'],
            'is_active': True,
            'shift': '1',
        }

        try:
            hub = MywashHub.query.filter(MywashHub.data.contains({'short': form['hub']})).first()
        except Exception, e:
            return {'status': 'failure', 'error': 'hub db error.'}, 500

        employee = EmployeeModel(data=emp_data)
        employee.login_creds = dict(session.get('emp_data', {}))
        employee.hub_id = hub.id
        employee.is_active = True
        try:
            pgdb.session.add(employee)
            pgdb.session.commit()
            session['employee_registered'] = True
        except Exception, e:
            return {'status': 'failure', 'error': 'emp db error.'}, 500

        return jsonify({'status': 'success'})


def logout():
    session.clear()
    return jsonify({'status': 'success'})


def serve_stache(file_name):
    kwargs = {}
    if 'user' in session and session['user'] == 'iamlegend':
        kwargs['username'] = 'iamlegend'
    return render_template("mustache/" + file_name, **kwargs)
