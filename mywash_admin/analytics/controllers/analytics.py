import datetime
import bson
import json
import calendar
import time

from collections import OrderedDict

from flask.ext.restful import Resource
from flask import jsonify, request

from mywash_admin import app
from mywash_admin import settings
from mywash_admin.lib import utils

db = app.config['MONGO_CLIENT']['dealsup']


class OrderAnalytics(Resource):
    def status(self):
        status_dict = {}
        for status in db.statuses.find():
            status_dict.update({status_name['name_id']: 0 for status_name in status['status']})
        return status_dict

    def order_data(self, start_date, end_date=None):
        try:
            date_list = [start_date]
            if end_date:
                while end_date not in date_list:
                    date = datetime.datetime.strptime(date_list[len(date_list) - 1], "%Y-%m-%d") + datetime.timedelta(days=1)
                    date_list.append(date.strftime('%Y-%m-%d'))

                schedules = db.schedules.find({
                    'schedule_date_new': {
                        '$gte': datetime.datetime.strptime(start_date, "%Y-%m-%d"),
                        '$lte': datetime.datetime.strptime(end_date, "%Y-%m-%d")
                    }, 'is_active': True
                })
            else:
                schedules = db.schedules.find({
                    'schedule_date_new': datetime.datetime.strptime(start_date, "%Y-%m-%d"),
                    'is_active': True
                })
            pickups = {}
            deliveries = {}
            for schedule in schedules:
                if schedule['is_pickup']:
                    pickups[schedule['_id']] = str(schedule['schedule_date_new'].date())
                else:
                    deliveries[schedule['_id']] = str(schedule['schedule_date_new'].date())
            order_status = {
                date: self.status() for date in date_list
            }
            orders = db.orders.find({
                '$or': [
                        {'pickup_id': {'$in': list(pickups)}},
                        {'delivery_id': {'$in': list(deliveries)}}
                    ],
            }, {'status': 1, 'delivery_id': 1, 'pickup_id': 1})
            print orders.count()
            for order in orders:
                try:
                    if order['pickup_id'] in pickups:
                        schedule_date = pickups[order['pickup_id']]
                        # print deliveries.pop(order['delivery_id'], None)
                        # del deliveries[order['delivery_id']]
                    elif order['delivery_id'] in deliveries:
                        schedule_date = deliveries[order['delivery_id']]
                        # del pickups[order['pickup_id']]
                        # print pickups.pop(order['pickup_id'], None)
                    else:
                        schedule_date = None
                    if schedule_date:
                        if type(order['status']) == int or type(order['status']) == float:
                            order['status'] = settings.DEPRECATED_STATUS_MAP[int(order['status'])]
                        order_status[schedule_date][order['status']] += 1
                    else:
                        print order
                except Exception as err:
                    print 'Error:', err, 'Order:', order
                    return {'status': 'failure', 'error': 'status error.'}, 500
            return order_status, 200
        except Exception as err:
            print 'Error:', err
            return {'status': 'failure', 'error': 'db error.'}, 500

    def get(self, from_date, to_date=''):
        start_time = time.time()
        if to_date and int(from_date.replace('-','')) > int(to_date.replace('-','')):
            return jsonify({'status': 'failure', 'error': 'Value error.'})
        res, status = self.order_data(from_date,to_date)
        result = {'data': []}
        for date, stats in res.items():
            result['data'].append({date:stats})
        result['data'].sort()
        print("Response within %s seconds" % (time.time() - start_time))
        return jsonify(result)


class UserAnalytics(Resource):
    def user_data(self, start_date, end_date=None):
        try:
            date_list = [start_date]

            if end_date:
                while end_date not in date_list:
                    date = datetime.datetime.strptime(date_list[len(date_list)-1], "%Y-%m-%d") + datetime.timedelta(days=1)
                    date_list.append(date.strftime('%Y-%m-%d'))

                users = db.users.find({
                        'createdAt': {
                           '$gte': datetime.datetime.strptime(start_date+" 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f"),
                           '$lte': datetime.datetime.strptime(end_date+" 23:59:59.999999", "%Y-%m-%d %H:%M:%S.%f")
                        }
                    })
            else:
                users = db.users.find({
                        'createdAt': {
                            '$gte': datetime.datetime.strptime(start_date+" 00:00:00.000000", "%Y-%m-%d %H:%M:%S.%f"), 
                            '$lte': datetime.datetime.strptime(start_date+" 23:59:59.999999", "%Y-%m-%d %H:%M:%S.%f")
                        }
                    })

            user_counts = {date: 0 for date in date_list}
            for user in users:
                created_date = str(user['createdAt'].date())
                if created_date in date_list:
                    user_counts[created_date]+=1
            return user_counts, 200
        except Exception as e:
            return {'status': 'failure', 'error': 'db error.'}, 500


    def get(self, from_date, to_date=None):
        start_time = time.time()
        if to_date is not None and int(from_date.replace('-','')) > int(to_date.replace('-','')):
            return jsonify({'status': 'failure', 'error': 'Value error.'})
        res, status = self.user_data(from_date,to_date)
        print res
        result = {'data':[]}
        for date, stats in res.items():
            result['data'].append({date:stats})
        result['data'].sort()
        print("Response within %s seconds" % (time.time() - start_time))
        return jsonify(result)


class OperationAnalytics(Resource):
    def daily_data(self, date):
        try:
            schedules = db.schedules.find({'schedule_date': date})
            schedule_orders = {}
            pickup_ids = []
            delivery_ids = []
            address_ids = []
            for schedule in schedules:
                address_ids.append(bson.ObjectId(schedule['address_id']))
                if schedule['is_pickup'] is True:
                    pickup_ids.append(schedule['_id'])
                else:
                    delivery_ids.append(schedule['_id'])
                schedule_orders[schedule['_id']] = schedule
            addresses = db.addresses.find({
                '_id': {'$in': address_ids}
            })
            address_dict = {}
            for address in addresses:
                address_dict[str(address['_id'])] = address['assigned_hub'] if 'assigned_hub' in address and address['assigned_hub'] is 2 else 1
            orders = db.orders.find({
                '$or': [
                        {'pickup_id': {'$in': pickup_ids}},
                        {'delivery_id': {'$in': delivery_ids}}
                    ],
            })
            order_analytics = OrderAnalytics()
            mrt_statuses_pickup = order_analytics.status()
            mrt_statuses_delivery = order_analytics.status()
            any_statuses_pickup = order_analytics.status()
            any_statuses_delivery = order_analytics.status()
            mrt_order_dict = {
                'pickup': 0,
                'delivery': 0,
            }
            any_order_dict = {
                'pickup': 0,
                'delivery': 0,
            }
            any_pickups = {
                'shift_1': 0,
                'shift_2': 0,
            }
            any_deliveries = {
                'shift_1': 0,
                'shift_2': 0,
            }
            mrt_pickups = {
                'shift_1': 0,
                'shift_2': 0,
            }
            mrt_deliveries = {
                'shift_1': 0,
                'shift_2': 0,
            }
            any_cancelled_or_rejected = 0
            mrt_cancelled_or_rejected = 0
            for order in orders:
                order['address_id'] = address_dict[order['address_id']]
                if order['address_id'] is 1:
                    if order['status'] in ['order_cancelled', 'order_rejected', 5, 6,]:
                        any_cancelled_or_rejected += 1
                    elif order['pickup_id'] in pickup_ids:
                        any_order_dict['pickup'] += 1
                        any_statuses_pickup[order['status']] += 1
                        if schedule_orders[order['pickup_id']]['schedule_time'] in ["8am - 10am", "10am - 12pm", "12pm - 2pm", "2pm - 4pm"]:
                            any_pickups['shift_1'] += 1
                        else:
                            any_pickups['shift_2'] += 1
                    elif order['delivery_id'] in delivery_ids:
                        any_order_dict['delivery'] += 1
                        any_statuses_delivery[order['status']] += 1
                        if schedule_orders[order['delivery_id']]['schedule_time'] in ["8am - 10am", "10am - 12pm", "12pm - 2pm", "2pm - 4pm"]:
                            any_deliveries['shift_1'] += 1
                        else:
                            any_deliveries['shift_2'] += 1
                else:
                    if order['status'] in ['order_cancelled', 'order_rejected', 5, 6,]:
                        mrt_cancelled_or_rejected += 1
                    elif order['pickup_id'] in pickup_ids:
                        mrt_order_dict['pickup'] += 1
                        mrt_statuses_pickup[order['status']] += 1
                        if schedule_orders[order['pickup_id']]['schedule_time'] in ["8am - 10am", "10am - 12pm", "12pm - 2pm", "2pm - 4pm"]:
                            mrt_pickups['shift_1'] += 1
                        else:
                            mrt_pickups['shift_2'] += 1
                    elif order['delivery_id'] in delivery_ids:
                        mrt_order_dict['delivery'] += 1
                        mrt_statuses_delivery[order['status']] += 1
                        if schedule_orders[order['delivery_id']]['schedule_time'] in ["8am - 10am", "10am - 12pm", "12pm - 2pm", "2pm - 4pm"]:
                            mrt_deliveries['shift_1'] += 1
                        else:
                            mrt_deliveries['shift_2'] += 1
            try:
                data = {
                    'any': {
                        'pickup': {
                            'total': any_order_dict['pickup'],
                            'shift_1': round((any_pickups['shift_1'] * 100.0) / any_order_dict['pickup'], 2),
                            'shift_2': round((any_pickups['shift_2'] * 100.0) / any_order_dict['pickup'], 2),
                            'pickup_percent': round((any_statuses_pickup['order_placed'] * 100.0) / any_order_dict['pickup'], 2),
                            'pickup_progress_percent': round((any_statuses_pickup['pickup_progress'] * 100.0) / any_order_dict['pickup'], 2),
                            'tagging_percentage': round((any_statuses_pickup['pickup_complete'] * 100.0) / any_order_dict['pickup'], 2),
                            'washing_percentage': round((any_statuses_pickup['washing'] * 100.0) / any_order_dict['pickup'], 2)
                        },
                        'delivery': {
                            'total': any_order_dict['delivery'],
                            'shift_1': round((any_deliveries['shift_1'] * 100.0) / any_order_dict['delivery'], 2),
                            'shift_2': round((any_deliveries['shift_2'] * 100.0) / any_order_dict['delivery'], 2),
                            'delivery_ready_percent': round((any_statuses_delivery['delivery_ready'] * 100.0) / any_order_dict['delivery'], 2),
                            'delivery_progress_percent': round((any_statuses_delivery['delivery_progress'] * 100.0) / any_order_dict['delivery'], 2),
                            'delivered_percentage': round((any_statuses_delivery['clothes_delivered'] * 100.0) / any_order_dict['delivery'], 2)
                        },
                        'cancelled/rejected': any_cancelled_or_rejected
                    },
                    'mrt': {
                        'pickup': {
                            'total': mrt_order_dict['pickup'],
                            'shift_1': round((mrt_pickups['shift_1'] * 100.0) / mrt_order_dict['pickup'], 2),
                            'shift_2': round((mrt_pickups['shift_2'] * 100.0) / mrt_order_dict['pickup'], 2),
                            'pickup_percent': round((mrt_statuses_pickup['order_placed'] * 100.0) / mrt_order_dict['pickup'], 2),
                            'pickup_progress_percent': round((mrt_statuses_pickup['pickup_progress'] * 100.0) / mrt_order_dict['pickup'], 2),
                            'tagging_percentage': round((mrt_statuses_pickup['pickup_complete'] * 100.0) / mrt_order_dict['pickup'], 2),
                            'washing_percentage': round((mrt_statuses_pickup['washing'] * 100.0) / mrt_order_dict['pickup'], 2)
                        },
                        'delivery': {
                            'total': mrt_order_dict['delivery'],
                            'shift_1': round((mrt_deliveries['shift_1'] * 100.0) / mrt_order_dict['delivery'], 2),
                            'shift_2': round((mrt_deliveries['shift_2'] * 100.0) / mrt_order_dict['delivery'], 2),
                            'delivery_ready_percent': round((mrt_statuses_delivery['delivery_ready'] * 100.0) / mrt_order_dict['delivery'], 2),
                            'delivery_progress_percent': round((mrt_statuses_delivery['delivery_progress'] * 100.0) / mrt_order_dict['delivery'], 2),
                            'delivered_percentage': round((mrt_statuses_delivery['clothes_delivered'] * 100.0) / mrt_order_dict['delivery'], 2)
                        },
                        'cancelled/rejected': mrt_cancelled_or_rejected
                    }
                }
            except Exception as e:
                print "mrt", str(e)
            return data
        except Exception, e:
            return {'status': 'failure', 'error': e}, 403

    def get(self, date=None):
        if date is None:
            current_datetime = str(utils.get_current_time())[:10]
        else:
            current_datetime = date
        return self.daily_data(current_datetime.replace('-', '/'))


class CohertAnalytics(Resource):
    def cohert_order_data(self):
        days_dict = {
            'Sunday': 0,
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5,
            'Saturday': 6
        }

        orders = db.orders.aggregate(
                    [{'$sort': {'created_date': 1}},
                    {'$group': 
                        {
                            '_id': "$user_id",
                            'created_date': {'$first': "$created_date"},
                            'count': {'$sum': 1},
                        }
                    }
                ])['result']

        count = 0
        for order in orders:
            count += order['count']

        date_order_dict = {}
        outer_count = 0
        inner_count = 0
        for order in orders:
            created_day = calendar.day_name[order['created_date'].weekday()]
            date = order['created_date'] - datetime.timedelta(days=days_dict[created_day])
            if str(date.date()) not in date_order_dict:
                inner_count += 1
                date_order_dict[str(date.date())] = set()
            outer_count += 1
            date_order_dict[str(date.date())].add(order['_id'])

        orderedDict = OrderedDict()
        for order in sorted(date_order_dict.keys()):
            orderedDict[order] = date_order_dict[order]

        date_order_dict = orderedDict

        last_dict_date = datetime.datetime.strptime(next(reversed(date_order_dict)), "%Y-%m-%d")
        last_date = last_dict_date + datetime.timedelta(days=7)

        print last_date
        data_list = []
        count = 0
        for key, value in date_order_dict.iteritems():
            data_dict = {'week': '', 'cohert': [], 'first_orders': ''}
            data_dict['week'] = key
            sunday = datetime.datetime.strptime(key, "%Y-%m-%d")
            next_sunday = datetime.datetime.strptime(key, "%Y-%m-%d")+datetime.timedelta(days=7)
            week_orders = db.orders.find({
                'created_date': {'$gte': sunday},
                'created_date': {'$lt': next_sunday},
                'user_id': {'$in': list(value)}
            })
            # print key, len(value), week_orders.count()
            count += week_orders.count()

            data_dict['first_orders'] = week_orders.count()
            d = sunday
            d2 = d + datetime.timedelta(days=7)
            while str(d2.date()) != str(last_date.date()):
                data = {}
                orders = db.orders.find({
                        'created_date': {'$gte': d}, 
                        'created_date': {'$lt': d2},
                        'user_id': {'$in': list(value)}
                    })
                data[str(d.date())] = orders.count()
                data['percent'] = (orders.count() * 100.0)/week_orders.count()
                d = d2
                d2 = d + datetime.timedelta(7)
                data_dict['cohert'].append(data)
            data_list.append(data_dict)
        return data_list, 200


    def cohert_user_data(self):
        days_dict = {
            'Sunday': 0,
            'Monday': 1,
            'Tuesday': 2,
            'Wednesday': 3,
            'Thursday': 4,
            'Friday': 5,
            'Saturday': 6
        }
        today = calendar.day_name[datetime.datetime.now().weekday()]
        last_date = datetime.datetime.now() + datetime.timedelta(days=days_dict['Saturday']-days_dict[today])
        orders = db.orders.aggregate(
                    [{'$sort': {'created_date': 1}},
                        {'$group': {'_id': "$user_id", 'created_date': {'$first': "$created_date"}}
                    }])['result']
        date_order_dict = {}
        for order in orders:
            if order['_id'] and order['created_date']:
                created_day = calendar.day_name[order['created_date'].weekday()]
                date = order['created_date'] - datetime.timedelta(days=days_dict[created_day])
                if str(date.date()) not in date_order_dict:
                    date_order_dict[str(date.date())] = set()
                date_order_dict[str(date.date())].add(order['_id'])

        data_list = []
        for key, value in date_order_dict.iteritems():
            data_dict = {'week': '', 'cohert': [], 'first_orders': ''}
            data_dict['week'] = key
            print 'key', key
            if key != '2015-06-07':
                sunday = datetime.datetime.strptime(key, "%Y-%m-%d")
                saturday = datetime.datetime.strptime(key, "%Y-%m-%d")+datetime.timedelta(days=days_dict['Saturday'])
                week_orders = db.orders.find({'user_id': {'$in': list(value)}})
                data_dict['first_orders'] = week_orders.count()
                d = saturday + datetime.timedelta(days=1)
                d2 = d + datetime.timedelta(days=days_dict['Saturday'])
                
                while str(d2.date()) != str(last_date.date()):
                    data = {}
                    users = db.users.find(
                            {'$and': [
                                    {'createdAt': {'$gte': d}}, 
                                    {'createdAt': {'$lte': d2}},
                                    {'user_id': {'$in': list(value)}}
                                ]
                        })
                    data[str(d.date())] = users.count()
                    data['percent'] = (users.count() * 100.0) /week_orders.count()
                    d = d2 + datetime.timedelta(days=1)
                    d2 = d + datetime.timedelta(days=days_dict['Saturday'])

                    data_dict['cohert'].append(data)
                
                data_list.append(data_dict)
        data_list.sort()
        return data_list, 200

    def get(self, argument):
        if argument == 'order':
            result, status = self.cohert_order_data()
        elif argument == 'user':
            result, status = self.cohert_user_data()

        # result, status = self.cohert_data()
        return result
