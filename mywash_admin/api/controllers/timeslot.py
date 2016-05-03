from flask.ext.restful import Resource
from flask import jsonify, request
from datetime import datetime
from sqlalchemy.sql import exists

import bson
import datetime
import pytz
import math
import copy
import json

from mywash_admin import app, db as pgdb
from api.models import TimeslotBlock
from mywash_admin.lib import utils

db = app.config['MONGO_CLIENT']['dealsup']

SLOTS_INDEX = {
    "8am - 10am": "1",
    "10am - 12pm": "2",
    "12pm - 2pm": "3",
    "2pm - 4pm": "4",
    "4pm - 6pm": "5",
    "6pm - 8pm": "6",
    "8pm - 10pm": "7"
}


class TimeSlot(Resource):
    def get(self, str_id=None):
        result = {}
        if str_id is not None:
            try:
                blocked_data = TimeslotBlock.query.filter(
                    (TimeslotBlock.str_id == str_id) &
                    (TimeslotBlock.is_active == True)
                ).first()
                result['date'] = str(blocked_data.blocked_date)
                result['slots'] = blocked_data.data['slots']
                result['type'] = blocked_data.data['type']
                result['_id'] = blocked_data.str_id

                return {'data': result}
            except Exception, e:
                return {'error': "db error.", 'status': "failure"}, 500

        try:
            utc_datetime = datetime.datetime.strptime(utils.get_current_time(), '%Y-%m-%d %H:%M:%S')
            blocked_timeslots = TimeslotBlock.query.filter(
                (TimeslotBlock.blocked_date>=utc_datetime.date()) &
                (TimeslotBlock.is_active==True)
            )
        except Exception, e:
            return {'error': "db error.", 'status': "failure"}, 500
        try:
            full_slots = db.timeslots.find_one({'active': 1}, {'_id': 0, 'active': 0})
        except Exception, e:
            return {'error': "db error.", 'status': "failure"}, 500

        timeslots_pickup = {}
        timeslots_delivery = {}
        filtered_slots = {}
        today_blocked = None
        for blocked in blocked_timeslots:
            available_slots = {key: full_slots[key] for key in set(full_slots) - set(blocked.data['slots'])}
            blocked_slots = blocked.data['slots']

            if not available_slots:
                available_slots = {'0': 'No Slots Are Available'}
            data = {}
            data['date'] = str(blocked.blocked_date)
            data['slots_available'] = available_slots
            data['slots_blocked'] = blocked_slots
            data['_id'] = blocked.str_id

            if blocked.data['type'] == 'pickup':
                if data['date'] == str(utc_datetime.date()):
                    today_blocked = data
                timeslots_pickup[data['date']] = data

            elif blocked.data['type'] == 'delivery':
                timeslots_delivery[data['date']] = data

        slot_now = (utc_datetime.hour - 6) / 2.0
        if slot_now < 7:
            slot_now = 0 if slot_now < 0 else int(math.ceil(slot_now))
            if today_blocked and str(utc_datetime.date()) == today_blocked['date']:
                for key in range((slot_now + 1), 8):
                    if str(key) in data['slots_available']:
                        filtered_slots[str(key)] = full_slots[str(key)]
            else:
                filtered_slots = {str(key): full_slots[str(key)] for key in range((slot_now+1),8)}
        if not filtered_slots:
            filtered_slots = {'0': 'No Slots Are Available'}

        result.update({
            'data': full_slots,
            'filtered_slots': filtered_slots,
            'timeslots_delivery': timeslots_delivery,
            'timeslots_pickup': timeslots_pickup,
            'date_today': str(utc_datetime.date())
        })
        return jsonify(result)

    def post(self):
        try:
            form = copy.deepcopy(request.form)
            if 'date' not in form or 'slots' not in form or 'type' not in form:
                return {'status': 'failure', 'error': 'Please provide a valid date, slots & type.'}, 403

            utc_datetime = datetime.datetime.strptime(utils.get_current_time(), '%Y-%m-%d %H:%M:%S')

            block_datetime = datetime.datetime.strptime(form['date'], '%Y-%m-%d')
            if block_datetime.date() < utc_datetime.date():
                return {'status': 'failure', 'error': 'Please provide a valid date.'}, 403
            try:
                timeslotblock = TimeslotBlock()
                timeslotblock.is_active = True
                timeslotblock.blocked_date = block_datetime.date()
                timeslotblock.data = {
                    'slots': {SLOTS_INDEX[slot]: slot for slot in json.loads(form['slots'])},
                    'type': form['type']
                }
                pgdb.session.add(timeslotblock)
                pgdb.session.commit()
                return {'status': 'success'}, 200
            except Exception as e:
                return {'status': 'failure', 'error': 'DB Error.'}, 403
        except Exception, e:
            return {'status': 'failure', 'error': 'Value Error.'}, 403

    def put(self, str_id):
        form = copy.deepcopy(request.form)
        print form
        action = form.get('action', '')
        try:
            if action not in ['edit', 'delete']:
                return {'status': 'failure', 'error': 'Action not defined'}, 403
            if 'date' not in form or 'slots' not in form or 'type' not in form:
                return {'status': 'failure', 'error': 'Please provide a valid date, slots & type.'}, 403

            try:
                timeslots = TimeslotBlock.query.filter(
                    (TimeslotBlock.str_id == str_id) &
                    (TimeslotBlock.is_active == True)
                ).first()
                data = copy.deepcopy(timeslots.data)

                if action == 'edit':
                    if 'slots' in form:
                        data['slots'] = {SLOTS_INDEX[slot]: slot for slot in json.loads(form['slots'])}
                    if 'type' in form:
                        data['type'] = form['type']
                    if 'date' in form:
                        timeslots.blocked_date = datetime.datetime.strptime(form['date'], '%Y-%m-%d').date()
                elif action == 'delete':
                    timeslots.is_active = False

                timeslots.last_modified = datetime.datetime.strptime(
                    utils.get_current_time(), '%Y-%m-%d %H:%M:%S')
                timeslots.data = data

                try:
                    pgdb.session.commit()
                    return {'status': 'success'}
                except Exception as e:
                    return {'status': 'failure', 'error': 'db error'}

            except Exception as e:
                print e
                return {'status': 'failure', 'error': 'Db error, date does not exist'}, 403

        except Exception, e:
            return {'status': 'failure', 'error': 'Db error, date doesnot exists'}, 403
