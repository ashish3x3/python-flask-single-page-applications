import traceback
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import csv
import datetime
from math import ceil
import boto
from boto.s3.key import Key
from mywash_admin import app, db as pgdb
import requests
from bson.objectid import ObjectId
import sendgrid
import os
# from io import BytesIO, StringIO
from StringIO import StringIO

db = app.config['MONGO_CLIENT']['dealsup']
log_db = app.config['MONGO_CLIENT']['mywash_logs']


def _upload_to_s3(aws_access_key_id, aws_secret_access_key, file, bucket, key):
    try:
        conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
        bucket = conn.get_bucket(bucket, validate=False)
        k = Key(bucket)
        k.key = key
        k.content_type = "text/csv"
        k.set_contents_from_file(file)
        k.set_acl('public-read')
        return True
    except Exception as e:
        print str(e)
        return False


def sendEmail(recepients, senderMail, subject, body, attach_path='', attach_name=''):
    sg = sendgrid.SendGridClient('mywash', 'dummy123')
    message = sendgrid.Mail()
    message.add_to(recepients)
    message.add_attachment(attach_name, attach_path)
    message.set_subject(subject)
    message.set_from(senderMail)
    message.set_from_name('MyWash')
    message.set_html(body)
    message.set_text(body)
    status, msg = sg.send(message)
    print status, msg, recepients
    return True


def send_report_email(paramDict={}):
    recepients = paramDict.get('recepients', '')
    if not recepients:
        print "No recepients email defined"
        return
    attach_name = None
    attach_path = None
    if paramDict.get('attach_name', ''):
        attach_name = paramDict['attach_name']
        attach_path = paramDict['attach_path']

    senderMail = paramDict.get("senderMail", "tech@mywash.com")

    return sendEmail(
        recepients=paramDict.get('recepients', ''),
        senderMail=senderMail,
        subject=paramDict.get('subject', 'New Message from MyWash'),
        body=paramDict.get('body', ''),
        attach_path=attach_path,
        attach_name=attach_name,
    )


def employees():
    try:
        emp_data = requests.get(app.config['SERVER_SELF'] + '/api/employee').json()['data']
        emp_dict = {}
        for emp in emp_data:
            try:
                emp_dict[emp['str_id']] = {
                    'name': emp['data']['name'],
                    'phone': ', '.join(emp['data']['phone'])
                    if type(emp['data']['phone']) == list else emp['data']['phone'],
                    'hub': emp.get('hub', {}).get('short', ''),
                    'emp_id': emp.get('emp_id', '')
                }
            except Exception as e:
                print str(e)
        return emp_dict
    except Exception as e:
        print str(e)
        return {}


def file_generation(data_list, field_names):
    fp = StringIO()
    writer = csv.DictWriter(fp, fieldnames=field_names)
    writer.writeheader()
    for data in data_list:
        try:
            writer.writerow(data)
        except Exception as e:
            print str(e), ' :@@@@@@@@@@@@@ '
            traceback.print_exc(file=sys.stdout)
    fp.seek(0)
    return fp


def daily_pickup_report(generate_file=False):
    date = str(datetime.datetime.utcnow().date())
    schedules = db.schedules.find({
        'is_active': True,
        'is_pickup': True,
        'schedule_date': date.replace('-', '/')
    })
    pickup_ids = []
    address_ids = []
    schedule_dict = {}
    emp_data = employees()
    for schedule in schedules:
        try:
            pickup_ids.append(schedule['_id'])
            schedule['_id'] = str(schedule['_id'])
            address_ids.append(ObjectId(schedule['address_id']))
            schedule_dict[schedule['_id']] = {
                'assigned_to': emp_data.get(schedule.get('assigned_to', ''), {}),
                'schedule_time': schedule['schedule_time'],
            }
        except Exception, e:
            print "Error in daily_pickup_report: @@@@@@@@" + str(e)
    orders = db.orders.find({
        'pickup_id': {'$in': pickup_ids},
        'status': {'$nin': [5, 6, 'order_cancelled', 'order_rejected']}
    })
    addresses = db.addresses.find({'_id': {'$in': address_ids}})
    address_dict = {}
    user_ids = []
    for address in addresses:
        address_dict[str(address['_id'])] = address.get('assigned_hub', 1)
        user_ids.append(address['user_id'])
    users = db.users.find({'user_id': {'$in': user_ids}})
    user_dict = {user['user_id']: user.get('name', '') for user in users}
    order_list = []
    for order in orders:
        data_dict = {}
        try:
            try:
                data_dict['order_id'] = order.get('order_id', str(order.get('_id', '')))
                data_dict['name'] = user_dict.get(order['user_id'], '')
                data_dict['phone'] = order.get('phone', '')
                data_dict['schedule_date'] = date
                data_dict['schedule_time'] = (schedule_dict.get(str(order['pickup_id'])))['schedule_time']
                data_dict['agent_name'] = (schedule_dict.get(str(order['pickup_id'])))['assigned_to'].get('name','')
                data_dict['agent_phone'] = (schedule_dict.get(str(order['pickup_id'])))['assigned_to'].get('phone','')
                data_dict['service_type'] = order.get('service_type', 'regular')
                data_dict['type'] = ', '.join(order.get('type', []))
                data_dict['status'] = order.get('status', '')
            except Exception ,e:
                print str(e),'!!!!!!!!!'
            if address_dict[order['address_id']] == 3:
                data_dict['hub'] = 'BTM'
            elif address_dict[order['address_id']] == 2:
                data_dict['hub'] = 'MRT'
            else:
                data_dict['hub'] = 'ANY'
            if 'failure_reason' in order and order['failure_reason']['pickup'] is not None:
                try:
                    reason_id = order['failure_reason']['pickup']
                    reason = requests.get(
                        app.config['SERVER_SELF'] + '/api/failurereason/' + reason_id
                    ).json()['data'][0]['reason']
                    data_dict['reason'] = reason.encode('ascii', 'ignore').decode('ascii') if reason is not None else ''
                except Exception as e:
                    data_dict['failure_reason'] = ''
                    print str(e), reason_id
            else:
                data_dict['failure_reason'] = ''
            order_list.append(data_dict)
        except Exception, e:
            print "Error in daily_pickup_report: ######## " + str(e)

    if generate_file:
        field_names = [
                "order_id",
                "name",
                "phone",
                "schedule_date",
                "schedule_time",
                "service_type",
                "type",
                "hub",
                "status",
                "failure_reason",
                "agent_name",
                "agent_phone",
                "reason"
        ]

        fp = file_generation(order_list, field_names)
        file_to_send = date + '_pickup_report.csv'
        try:
            if not _upload_to_s3(
                app.config['AWS_CREDS']['access_key_id'],
                app.config['AWS_CREDS']['secret_access_key'],
                fp,
                app.config['AWS_CREDS']['bucket_reports'],
                file_to_send
            ):
                return {'status': 'failure', 'error': 's3 error'}, 403
        except Exception as e:
            return {'status': 'failure', 'error': 'pdf error'}, 403

        try:
            url = app.config['AWS_CREDS']['s3_uri'] + '/' + app.config['AWS_CREDS']['bucket_reports'] + '/' + file_to_send
            send_report_email({
                "recepients": 'abhilash@mywash.com' if app.config['DEBUG'] else 'ops@mywash.com',
                "senderMail": 'noreply@mywash.com',
                "subject": 'Daily Pickup Reports %s' % date,
                "body": url
            })
            
        except Exception,e:
            print 'emaillll',str(e)
            traceback.print_exc(file=sys.stdout)
        finally:
            try:
                if os.path.isfile(file_to_send):
                    os.remove(file_to_send)
            except Exception, e:
                print e
    else:
        return order_list


def daily_delivery_report(generate_file=False):
    print 'Daily delivery report generating'
    try:
        date = str(datetime.datetime.utcnow().date())
        # date = '2015-08-25'
        schedules = db.schedules.find({
            'is_active': True,
            'is_pickup': False,
            'schedule_date': date.replace('-', '/')
        })
        delivery_ids = []
        address_ids = []
        schedule_dict = {}
        emp_data = employees()
        for schedule in schedules:
            try:
                delivery_ids.append(schedule['_id'])
                schedule['_id'] = str(schedule['_id'])
                address_ids.append(ObjectId(schedule['address_id']))
                schedule_dict[schedule['_id']] = {
                    'assigned_to': emp_data.get(schedule.get('assigned_to', ''), {}),
                    'schedule_time': schedule['schedule_time'],
                }
            except Exception, e:
                print "Error in daily_delivery_report: " + str(e)
        orders = db.orders.find({
            'delivery_id': {'$in': delivery_ids},
            'status': {'$nin': [5, 6, 'order_cancelled', 'order_rejected']}
        })
        addresses = db.addresses.find({'_id': {'$in': address_ids}})
        address_dict = {}
        user_ids = []
        for address in addresses:
            address_dict[str(address['_id'])] = address.get('assigned_hub', 1)
            user_ids.append(address['user_id'])
        users = db.users.find({'user_id': {'$in': user_ids}})
        user_dict = {user['user_id']: user.get('name', '') for user in users}
        order_list = []
        for order in orders:
            data_dict = {}
            try:
                data_dict['order_id'] = order.get('order_id', str(order.get('_id', '')))
                data_dict['name'] = user_dict.get(order['user_id'], '')
                data_dict['phone'] = order.get('phone', '')
                data_dict['schedule_date'] = date
                data_dict['schedule_time'] = (schedule_dict.get(str(order['delivery_id'])))['schedule_time']
                data_dict['agent_name'] = (schedule_dict.get(str(order['delivery_id'])))['assigned_to'].get('name', '')
                data_dict['agent_phone'] = (schedule_dict.get(str(order['delivery_id'])))['assigned_to'].get('phone', '')
                data_dict['service_type'] = order.get('service_type', 'regular')
                data_dict['type'] = ', '.join(order.get('type', []))
                data_dict['status'] = order.get('status', '')
                if address_dict[order['address_id']] == 3:
                    data_dict['hub'] = 'BTM'
                elif address_dict[order['address_id']] == 2:
                    data_dict['hub'] = 'MRT'
                else:
                    data_dict['hub'] = 'ANY'
                if 'failure_reason' in order and \
                (order['failure_reason']['delivery'] is not None or
                        order['failure_reason']['partial_payment'] is not None):
                    try:
                        reason_id = order['failure_reason']['delivery']
                        reason_id = order['failure_reason']['partial_payment']
                        reason = requests.get(
                            app.config['SERVER_SELF'] + '/api/failurereason/' + reason_id
                        ).json()['data'][0]['reason']
                        data_dict['reason'] = reason.encode('ascii', 'ignore').decode('ascii') if reason is not None else ''
                        print reason
                    except Exception as e:
                        data_dict['failure_reason'] = ''
                        print str(e), reason_id
                else:
                    data_dict['failure_reason'] = ''
                data_dict['invoice_amount'] = float(order.get('total_price', 0))
                data_dict['cash_collected'] = ceil(order.get('cash_collected', 0)) if order.get('cash_collected', 0) != 'online_paid' else 0
                data_dict['to_be_collected'] = ceil(order.get('total_price', 0)) if order.get('cash_collected', 0) != 'online_paid' else 0
                order_list.append(data_dict)
            except Exception, e:
                print "Error in daily_delivery_report: " + str(e)
        if generate_file:
            field_names = [
                "order_id",
                "name",
                "phone",
                "schedule_date",
                "schedule_time",
                "service_type",
                "type",
                "hub",
                "status",
                "failure_reason",
                "agent_name",
                "agent_phone",
                "invoice_amount",
                "to_be_collected",
                "cash_collected",
                "reason"
            ]
            fp = file_generation(order_list, field_names)
            file_to_send = date + '_delivery_report.csv'
            try:
                try:
                    if not _upload_to_s3(
                        app.config['AWS_CREDS']['access_key_id'],
                        app.config['AWS_CREDS']['secret_access_key'],
                        fp,
                        app.config['AWS_CREDS']['bucket_reports'],
                        file_to_send
                        ):
                        return {'status': 'failure', 'error': 's3 error'}, 403
                except Exception as e:
                    return {'status': 'failure', 'error': 'pdf error'}, 403

                url = app.config['AWS_CREDS']['s3_uri'] + '/' + app.config['AWS_CREDS']['bucket_reports'] + '/' + file_to_send
                send_report_email({
                    "recepients": 'abhilash@mywash.com' if app.config['DEBUG'] else 'ops@mywash.com',
                    "senderMail": 'noreply@mywash.com',
                    "subject": 'Daily Delivery reports %s' % date,
                    "body": url
                })
                
            except Exception,e:
                print 'emaillll',str(e)
                traceback.print_exc(file=sys.stdout)
            finally:
                try:
                    if os.path.isfile(file_to_send):
                        os.remove(file_to_send)
                except Exception, e:
                    print e
        else:
            return order_list
    except Exception as e:
        print "Error in daily_delivery_report: " + str(e)


def staff_performance(generate_file=False):
    print 'Daily staff performance  report generating'
    try:
        date = str((datetime.datetime.today() - datetime.timedelta(days=1)).date())
        result = employees()
        emp_data = {data.get('phone'): data for str_id, data in result.items()}
        schedule_deliveries = daily_delivery_report()
        delivery_data = {}

        for schedule in schedule_deliveries:
            try:
                if schedule.get('agent_phone') in delivery_data:
                    try:
                        delivery_data.get(schedule.get('agent_phone')).get('status').append(schedule.get('status'))
                    except Exception,e:
                        print 'qqqqqqqq',str(e)
                else:
                    try:
                        delivery_data[schedule.get('agent_phone')] = {
                            'status': [schedule.get('status')],
                            'hub': schedule.get('hub'),
                            'emp_id': '',
                            'name': schedule.get('agent_name'),
                            'phone': schedule.get('agent_phone'),
                            'success': 0,
                            'performance': 0,
                        }

                        if emp_data.get(schedule.get('agent_phone')) != None:
                            delivery_data.get(schedule.get('agent_phone')).update(emp_id = emp_data.get(schedule.get('agent_phone')).get('emp_id',''))

                    except Exception,e:
                        print 'jjjjjjj',str(e)
            except Exception,e:
                print 'uuuuuuuu',str(e)

        employee_deliveries = []
        for key, value in delivery_data.items():
            try:
                statuses = value.pop('status')
                count = 0
                total = len(statuses)
                for status in statuses:
                    if status == 'delivery_failed':
                        count += 1
                value['assigned'] = total
                value['success'] = total - count
                value['performance'] = (value.get('success') * 100) / value.get('assigned')
                employee_deliveries.append(value)
            except Exception,e:
                print 'kkkkkkkkkkk...',str(e)
        schedule_pickups = daily_pickup_report()
        pickup_data = {}
        for schedule in schedule_pickups:
            try:
                if schedule.get('agent_phone') in pickup_data:
                    pickup_data.get(schedule.get('agent_phone')).get('status').append(schedule.get('status'))
                else:
                    try:
                        pickup_data[schedule.get('agent_phone')] = {
                            'status': [schedule.get('status')],
                            'hub': schedule.get('hub'),
                            'emp_id': '',
                            'name': schedule.get('agent_name'),
                            'phone': schedule.get('agent_phone'),
                            'success': 0,
                            'performance': 0,
                        }
                        try:
                            if emp_data.get(schedule.get('agent_phone')) != None:
                                pickup_data.get(schedule.get('agent_phone')).update(emp_id = emp_data.get(schedule.get('agent_phone')).get('emp_id',''))
                        except Exception,e:
                            print 'wwww',str(e)

                    except Exception,e:
                        print 'jjjjjjj',str(e)
            except Exception,e:
                print 'mmmmmmmm...',str(e)
        employee_pickups = []
        print ''
        for key, value in pickup_data.items():
            try:
                statuses = value.pop('status')
                count = 0
                total = len(statuses)
                for status in statuses:
                    if status == 'delivery_failed':
                        count += 1
                value['assigned'] = total
                value['success'] = total - count
                if value['assigned'] !=0:
                    value['performance'] = (value.get('success') * 100) / value.get('assigned')
                employee_pickups.append(value)
            except Exception,e:
                print 'bbbbbbbbbbb...',str(e)

        if generate_file:
            field_names = [
                "hub",
                "emp_id",
                "name",
                "phone",
                "assigned",
                "success",
                "performance",
            ]
            
            pickup_fp = file_generation(employee_pickups, field_names)
                 
            delivery_fp = file_generation(employee_deliveries, field_names)

            file_to_send = date + '_pickup_staff_report.csv'
            try:
                try:
                    if not _upload_to_s3(
                        app.config['AWS_CREDS']['access_key_id'],
                        app.config['AWS_CREDS']['secret_access_key'],
                        pickup_fp,
                        app.config['AWS_CREDS']['bucket_reports'],
                        file_to_send
                    ):
                        return {'status': 'failure', 'error': 's3 error'}, 403
                except Exception as e:
                    return {'status': 'failure', 'error': 'pdf error'}, 403

                url = app.config['AWS_CREDS']['s3_uri'] + '/' + app.config['AWS_CREDS']['bucket_reports'] + '/' + file_to_send
                send_report_email({
                    "recepients": 'ashish.singh@mywash.com',
                    "senderMail": 'noreply@mywash.com',
                    "subject": 'Pickup Staff Reports',
                    "body": url
                })
            except Exception, e:
                print 'emaillll',str(e)
                traceback.print_exc(file=sys.stdout)

            try:
                if os.path.isfile(file_to_send):
                    os.remove(file_to_send)
            except Exception, e:
                print e
            file_to_send = date + '_delivery_staff_report.csv'
            try:
                try:
                    if not _upload_to_s3(
                        app.config['AWS_CREDS']['access_key_id'],
                        app.config['AWS_CREDS']['secret_access_key'],
                        delivery_fp,
                        app.config['AWS_CREDS']['bucket_reports'],
                        file_to_send
                    ):
                        return {'status': 'failure', 'error': 's3 error'}, 403
                except Exception as e:
                    return {'status': 'failure', 'error': 'csv error'}, 403

                url = app.config['AWS_CREDS']['s3_uri'] + '/' + app.config['AWS_CREDS']['bucket_reports'] + '/' + file_to_send
                send_report_email({
                    "recepients": 'ashish.singh@mywash.com',
                    "senderMail": 'noreply@mywash.com',
                    "subject": 'Delivery Staff Reports',
                    "body": url
                })
                
            except Exception,e:
                print 'emaillll',str(e)
                traceback.print_exc(file=sys.stdout)
            try:
                if os.path.isfile(file_to_send):
                    os.remove(file_to_send)
            except Exception, e:
                print e

        else:
            return employee_pickups, employee_deliveries
    except Exception as e:
        print "Error in staff_performance(): llmlmlmlmlm " + str(e)


def hub_performance():
    try:
        date = str((datetime.datetime.today() - datetime.timedelta(days=1)).date())
        # date = '2015-08-25'
        schedule_deliveries = daily_delivery_report()
        hub_data = {}
        for schedule in schedule_deliveries:
            if schedule.get('hub') in hub_data:
                hub_data.get(schedule.get('hub')).get('status').append(schedule.get('status'))
                hub_data.get(schedule.get('hub'))['total_collectable_amount'] += schedule.get('to_be_collected')
                hub_data.get(schedule.get('hub'))['total_cash_collected'] += schedule.get('cash_collected')
            else:
                hub_data[schedule.get('hub')] = {
                    'status': [schedule.get('status')],
                    'total_collectable_amount': schedule.get('to_be_collected'),
                    'total_cash_collected': schedule.get('cash_collected'),
                    'leakage': 0,
                    'total_deliveries': 0,
                    'delivery_successfull': 0,
                    'delivery_performance': 0,
                    'deliveries_assigned': 0,
                    'deliveries_done': 0,
                    'delivery_staff_performance': 0,
                }
        for key, value in hub_data.items():
            statuses = value.pop('status')
            total = len(statuses)
            count = 0
            for status in statuses:
                if status == 'delivery_failed':
                    count += 1
                value['total_deliveries'] = total
                value['delivery_successfull'] = total - count
                if total != 0:
                    value['delivery_performance'] = (100 * value.get('delivery_successfull')) / total
                value['hub'] = key
        schedule_pickups = daily_pickup_report()
        for schedule in schedule_pickups:
            if schedule.get('hub') in hub_data and 'status' in hub_data.get(schedule.get('hub')):
                hub_data.get(schedule.get('hub')).get('status').append(schedule.get('status'))
            else:
                data = {
                    'status': [schedule.get('status')],
                    'total_pickups': 0,
                    'pickup_successfull': 0,
                    'pickup_performance': 0,
                    'pickup_assigned': 0,
                    'pickup_done': 0,
                    'pickup_staff_performance': 0,
                }
                hub_data[schedule.get('hub')].update(data)
        for key, value in hub_data.items():
            statuses = value.pop('status')
            total = len(statuses)
            count = 0
            for status in statuses:
                if status == 'pickup_failed':
                    count += 1
                value['total_pickups'] = total
                value['pickup_successfull'] = total - count
                if total != 0:
                    value['pickup_performance'] = (100 * value.get('pickup_successfull')) / total
        pickup_staff_data, delivery_staff_data = staff_performance()
        for data in pickup_staff_data:
            if data.get('hub') in hub_data:
                hub_data.get(data.get('hub'))['pickup_assigned'] += data['assigned']
                hub_data.get(data.get('hub'))['pickup_done'] += data['success']
        for data in delivery_staff_data:
            if data.get('hub') in hub_data:
                hub_data.get(data.get('hub'))['deliveries_assigned'] += data['assigned']
                hub_data.get(data.get('hub'))['deliveries_done'] += data['success']
        data_list = []
        for key, value in hub_data.items():
            if value.get('pickup_assigned') !=0:
                value['pickup_staff_performance'] = (
                    100 * value.get('pickup_done')
                ) / value.get('pickup_assigned')
            if value.get('deliveries_assigned') !=0:
                value['delivery_staff_performance'] = (
                    100 * value.get('deliveries_done')
                ) / value.get('deliveries_assigned')
            data_list.append(value)
        field_names = [
            'hub',
            'total_pickups',
            'pickup_successfull',
            'pickup_performance',
            'pickup_assigned',
            'pickup_done',
            'pickup_staff_performance',
            'total_collectable_amount',
            'total_cash_collected',
            'leakage',
            'total_deliveries',
            'delivery_successfull',
            'delivery_performance',
            'deliveries_assigned',
            'deliveries_done',
            'delivery_staff_performance',
        ]
        fp = file_generation(data_list, field_names)

        file_to_send = date + 'hub_report.csv'
        try:
            try:
                fp = open(file_to_send, 'r')
                if not _upload_to_s3(
                    app.config['AWS_CREDS']['access_key_id'],
                    app.config['AWS_CREDS']['secret_access_key'],
                    fp,
                    app.config['AWS_CREDS']['bucket_reports'],
                    file_to_send
                ):
                    return {'status': 'failure', 'error': 's3 error'}, 403
            except Exception as e:
                return {'status': 'failure', 'error': 'csv error'}, 403

                url = app.config['AWS_CREDS']['s3_uri'] + '/' + app.config['AWS_CREDS']['bucket_reports'] + '/' + file_to_send
                send_report_email({
                    "recepients": 'ashish.singh@mywash.com',
                    "senderMail": 'noreply@mywash.com',
                    "subject": 'Hub Reports',
                    "body": url
                })
                
            except Exception,e:
                print 'emaillll',str(e)
                traceback.print_exc(file=sys.stdout)
            finally:
                try:
                    if os.path.isfile(file_to_send):
                        os.remove(file_to_send)
                except Exception, e:
                    print e
        except Exception, e:
            print 'emaillll', str(e)
            traceback.print_exc(file=sys.stdout)
    except Exception, e:
        print "Error in hub_performance(): " + str(e)


if __name__ == '__main__':
    daily_pickup_report(True)
    daily_delivery_report(True)
    # staff_performance(True)
    # hub_performance()
    # a = file_generation([{'one': '1', 'two': '2'}, {'one': '1', 'two': '2'}], ['one', 'two'], 'test_report.csv')
    # _upload_to_s3(
    #     app.config['AWS_CREDS']['access_key_id'],
    #     app.config['AWS_CREDS']['secret_access_key'],
    #     a,
    #     app.config['AWS_CREDS']['bucket_reports'],
    #     'test_report.csv'
    # )
