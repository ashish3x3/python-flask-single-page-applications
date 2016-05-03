import sendgrid
import logging
import copy
from flask import render_template
from mywash_admin import app
import bson
import datetime
import requests
import urllib
from api.models import Employee as EmployeeModel, MywashHub, Partner
from api.controllers.employees import Employee
from mywash_admin import celery
import json
from mywash_admin import settings

db = app.config['MONGO_CLIENT']['dealsup']


def sendmailWithTemplate(paramDict={}):
    recepients = paramDict.get('recepients', '')
    if not recepients:
        print "No recepients email defined"
        return
    # template = env.get_template(paramDict.get('templateName', ''))
    # html = template.render(paramDict)
    html = render_template(paramDict.get('templateName'), **paramDict)
    attach_name = None
    attach_path = None
    if paramDict.get('attach_name', ''):
        attach_name = paramDict['attach_name']
        attach_path = paramDict['attach_path']
    categories = paramDict.get('categories', [])
    if not isinstance(categories, list):
        categories = []

    senderMail = paramDict.get("senderMail", "team@mywash.in")

    return sendmail.delay(
        recepients=paramDict.get('recepients', ''),
        recepientName=paramDict.get('recepientName', ''),
        senderMail=senderMail,
        subject=paramDict.get('subject', 'New Message from MyWash'),
        body=paramDict.get('body', ''),
        html=html,
        attach_path=attach_path,
        attach_name=attach_name,
        categories=categories
    )


@celery.task
def sendmail(recepients, recepientName, senderMail='noreply@mywash.in', senderName='MyWash',
    subject='MyWash', body='', html='', attach_path='', attach_name='', categories=[]):
    pass


def get_order_email(order_id):
    try:
        order = db.orders.aggregate(
            {'$match': {'_id': bson.ObjectId(order_id)}}
        )['result'][0]

        users = db.users.aggregate(
            {'$match': {'user_id': order.get('user_id')}}
        )['result'][0]

        pickup_data = db.schedules.aggregate(
            {'$match': {'_id': bson.ObjectId(order.get("pickup_id"))}}
        )['result'][0]
        pickup_data['_id'] = str(pickup_data['_id'])

        delivery_data = db.schedules.aggregate(
            {'$match': {'_id': bson.ObjectId(order.get("delivery_id"))}}
        )['result'][0]
        delivery_data['_id'] = str(delivery_data['_id'])

        address = db.addresses.aggregate(
            {'$match': {'_id': bson.ObjectId(order.get("address_id"))}}
        )['result'][0]

        address['_id'] = str(address['_id'])

        result = copy.deepcopy(order)
        for k, v in order.items():
            if isinstance(v, bson.ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime.date):
                result[k] = v.strftime("%b %d %Y %H:%M")
        if result:
            washtypes = order.get('type')
            washtype_str = ""
            if isinstance(washtypes, list):
                washtype_str = ', '.join([app.config['SERVICE_TYPE_DICT'][wash] for wash in washtypes])
            else:
                washtype_str = washtypes
            try:
                result.update({"delivery": delivery_data})
                result.update({"pickup": pickup_data})
                result.update({"address": address})
                result.update({"user": copy.deepcopy(users.get('name'))})
                result.update({"phone": copy.deepcopy(users.get('phone'))})
                result.update({"type": washtype_str})
                result.update({"status": app.config['ORDER_DICT'].get(str(order.get("status")),"")})
                result.update({"orderid": order_id})
                result.update({"real_order_id": order.get('order_id')})
                result.update({"pickup_address": address})
                result.update({"clothes": copy.deepcopy(dict(enumerate(order.get("order_items"))))})
                result.update({"ordervalue": order.get("order_price")})
                result.update({"credits": order.get("credits_applied")})
                result.update({"totalpayable": order.get("order_price", 0) - order.get("credits_applied",0)})
            except Exception as e:
                print "Failed to get order email with exception ", str(e)
        return result
    except Exception as e:
        print "Failed to Fetch order with exception ", str(e)
    return None


def email_welcome(data):
    paramDict = {}
    paramDict.update({'emails': {'user': data.get("name", "")}})
    paramDict.update({
        'recepients': data.get("email"),
        'recepientName': data.get("name"),
        'senderMail': "team@mywash.in",
        'templateName': 'emails/welcome.html',
        'subject': 'Welcome to Mywash.in'
    })
    logging.info("Sending Welcome Email with data ")
    logging.info(paramDict)
    sendmailWithTemplate(paramDict=paramDict)
    send_mywash_email(paramDict, subject="New User Joined Alert")


def send_mywash_email(paramDict, subject="Default Subject"):
    paramDict.update({"recepients": "team@mywash.in" if not app.config['DEBUG'] else 'tech@mywash.com'})
    paramDict.update({"subject": subject})
    sendmailWithTemplate(paramDict=paramDict)


def email_order_placed(data):
    paramDict = {}
    paramDict.update({'emails': get_order_email(data.get("order_id"))})
    paramDict.update({
        'recepients': data.get("email"),
        'recepientName': data.get("name"),
        'senderMail': "team@mywash.in",
        'templateName': 'emails/order_placed.html',
        'subject': 'You Order is Placed'
    })
    logging.info(paramDict)
    sendmailWithTemplate(paramDict=paramDict)
    send_mywash_email(paramDict, subject="New Order Alert")


def email_order_cancelled(data):
    paramDict = {}
    paramDict.update({'emails':copy.deepcopy(get_order_email(data.get("order_id")))})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/order-status5.jinja',
                        'subject':'Your order Invoice'})

    logging.info(paramDict)
    sendmailWithTemplate(paramDict=paramDict)
    send_mywash_email(paramDict, subject="Order Cancelled Alert")


@celery.task
def send_message_ozonetel(sid, token, sms_from, sms_to, sms_body):
    dyncamic_data = urllib.urlencode({
            'loginid': sid,
            'password': token,
            'send_to': sms_to,
            'msg': sms_body
        })
    static_data = "&msg_type=text&auth_scheme=plain&v=1.1&format=text&method=sendMessage"
    sms = "http://enterprise.smsgupshup.com/GatewayAPI/rest?" + dyncamic_data + static_data
    r = requests.post(sms)
    return True if r.status_code == 200 else False

@celery.task
def send_message_sol_infini(sid, token, sms_from, sms_to, sms_body):
    dyncamic_data = urllib.urlencode({
            'to': sms_to,
            'message': sms_body
        })
    sms = "http://alerts.solutionsinfini.com/api/v3/index.php?method=sms&api_key=Aade769041b6835b6fe5271f89a227a4d&sender=MYWASH&format=json&custom=1,2&flash=0&" + dyncamic_data
    r = requests.post(sms)
    return True if r.status_code == 200 else False

@celery.task
def send_message_exotel(sid, token, sms_from, sms_to, sms_body):
    pass

@celery.task
def send_parse_notification(installation_id, title, alert_msg, msg_type, order_id, parse_creds):
    pass


def mywash_order_transactional_sms(phone, text, partner_id=None):

    is_sms_block = False
    if partner_id is not None:
        partner = Partner.query.filter(
            (Partner.str_id == partner_id) &
            (Partner.is_active == True)
        ).first()
        is_sms_block = partner.is_sms_block
        if partner.email == 'laundry@localoye.com':
            text = "Hi %s.Thank you." % \
                text.replace('mywash', 'localoye').replace('MyWash', 'localoye').replace('Mywash', 'localoye')
            print ">>>>>>>>>>>", text
            return requests.post(
                'https://twilix.exotel.in/v1/Accounts/{sid}/Sms/send.json'.format(sid='localoye1'),
                auth=('localoye1', '7de67f061e376dcf6e84dc0c49bb5592090d3e31'),
                data={
                    'From': "localoye",
                    'To': app.config['ADMIN']['phone'] if app.config['DEBUG'] else phone,
                    'Body': text.encode('utf-8')
                }
            )
    elif not is_sms_block:
        func = None
        if app.config['SMS_PROVIDER'] == 'ozone':
            func = send_message_ozonetel
        elif app.config['SMS_PROVIDER'] == 'exotel':
            text = "Hi %s.Thank you." % text
            func = send_message_exotel
        elif app.config['SMS_PROVIDER'] == 'solinifi':
            func = send_message_sol_infini
        phone = app.config['ADMIN']['phone'] if app.config['DEBUG'] else phone
        return func.delay(
            app.config['SMS_CONF']['SID'],
            app.config['SMS_CONF']['TOKEN'],
            sms_from="mywash",
            sms_to=phone,
            sms_body=text.encode('utf-8')
        )


def sms_order_placed(data):
    paramDict = {}
    paramDict.update({'emails': copy.deepcopy(get_order_email(data.get("order_id")))})
    logging.info("Sending Order SMS with data ")
    logging.info(paramDict)
    text = "Hi " + data.get('name', "user") + " ,we have received your order. Mywash agent will be there between "+ paramDict["emails"].get("pickup").get("schedule_time") +" on "+ paramDict["emails"].get("pickup").get("schedule_date") +" for the pickup."
    mywash_order_transactional_sms(paramDict["emails"].get("phone"), text)


def election_closing_sms(data):
    paramDict = {}
    paramDict.update({'emails': copy.deepcopy(get_order_email(data.get("order_id")))})
    logging.info("Sending Order SMS with data ")
    logging.info(paramDict)
    text = "Hi " + data.get('name', "user") + ", due to elections we are closed on 22nd. We will pick your order tomorrow between "+ paramDict["emails"].get("pickup").get("schedule_time") + ". Apology for the inconvenience."
    mywash_order_transactional_sms(paramDict["emails"].get("phone"), text)


def sms_alert_agent_pickup(data):
    paramDict = {}
    paramDict.update({'emails':copy.deepcopy(get_order_email(data.get("order_id")))})
    text = "Hi "+data.get('name',"user") +", mywash agent is on the way for the pickup between "+paramDict["emails"].get("pickup")["result"][0].get("schedule_time")+". Reach us at 08039591212 for queries."
    logging.info("Sending agent pickup alert for ")
    logging.info(data)
    mywash_order_transactional_sms(data.get("phone"),text)


def sms_order_cancelled(data):
    paramDict = {}
    paramDict.update({'emails': copy.deepcopy(get_order_email(data.get("order_id")))})
    logging.info(paramDict)
    text = "Hi " + data.get("name", "user") + ", your order has been cancelled. We hope to serve you sometime soon. Click this link to http://bit.ly/1wKC6tj place a new order."
    mywash_order_transactional_sms(paramDict["emails"].get("phone"), text)


def notification_alert_agent_pickup(emp_id, order_id):
    # emp_phone = phone
    notification = None
    employee = None
    try:
        employee = Employee()
        employee = json.loads(employee.get(emp_id=emp_id).response[0])['data'][0]
        if 'notification' in employee and employee['notification']:
            notification = employee['notification']
    except Exception, e:
        print e
        # return {'status': 'failure', 'error': 'db error.'}, 500
    title = "New Pickup Assigned!"
    alert_message = employee['data']['name'] + "," + order_id + " is assigned for pickup"
    if notification and 'installation_id' in notification and notification['installation_id']:
        send_parse_notification.delay(
            notification['installation_id'], title, alert_message, "agent_pickup", order_id, settings.PARSE_CREDS
        )


def notification_alert_agent_delivery(emp_id, order_id):
    # emp_phone = phone
    notification = None
    employee = None
    try:
        employee = Employee()
        employee = json.loads(employee.get(emp_id=emp_id).response[0])['data'][0]
        if 'notification' in employee and employee['notification']:
            notification = employee['notification']
    except Exception, e:
        print e
        # return {'status': 'failure', 'error': 'db error.'}, 500
    title = "New Delivery Assigned!"
    alert_message = employee['data']['name'] + "," + order_id + " is assigned for delivery"
    if notification and 'installation_id' in notification and notification['installation_id']:
        send_parse_notification.delay(
            notification['installation_id'], title, alert_message, "agent_delivery", order_id, settings.PARSE_CREDS
        )


def notification_alert_agent_order_payment_complete(emp_id, order_id):
    # emp_phone = phone
    notification = None
    employee = None
    try:
        employee = Employee()
        employee = json.loads(employee.get(emp_id=emp_id).response[0])['data'][0]
        if 'notification' in employee and employee['notification']:
            notification = employee['notification']
    except Exception, e:
        print e
        # return {'status': 'failure', 'error': 'db error.'}, 500
    title = order_id + " 's Payment Done!"
    alert_message = employee['data']['name'] + "," + order_id + " 's payment successful!"
    if notification and 'installation_id' in notification and notification['installation_id']:
        send_parse_notification.delay(
            notification['installation_id'], title, alert_message, "order_payment_success", order_id, settings.PARSE_CREDS
        )

# def notification_alert_agent_delivery(emp_id):
#     # emp_phone = phone
#     notification = None
#     try:
#         emp = EmployeeModel.query.filter(
#                 EmployeeModel.str_id == emp_id & EmployeeModel.is_active == True
#             ).first()
#         if not emp:
#             return {'status': 'failure', 'error': "Unauthorized Number!\nPlease Contact Your Manager."}, 404
#         notification = copy.deepcopy(emp.notification)
#     except Exception, e:
#         print e
#         return {'status': 'failure', 'error': 'db error.'}, 500
#     title = "New Delivery Assigned!"
#     alert_message = "Assigned New Delivery"
#     send_parse_notification(notification['installation_id'], title, alert_message)
