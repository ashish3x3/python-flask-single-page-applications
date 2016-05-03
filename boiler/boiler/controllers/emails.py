import datetime
from flask import render_template,session, make_response, request, jsonify, json
from boiler.models.dao import itemsDAO
from boiler.models.dao import ordersDAO
from boiler.models.dao import usersDAO
from boiler.renderer import commonrender
import copy,logging, requests
from boiler import emailer
from boiler.celery_app.celeryconfig import celery
from threading import Thread
from boiler import app

@celery.task
def send_mywash_email(paramDict,subject="Default Subject"):
    senderMail="veera@mywash.com" if paramDict.get("service_type") == "express" else "team@mywash.in"

    paramDict.update({"recepients":senderMail})
    paramDict.update({"subject":subject})
    emailer.sendmailWithTemplate(paramDict = paramDict)

@celery.task
def email_welcome(data):
    paramDict={}
    paramDict.update({'emails': {'user': data.get("name"," ").split(' ')[0]}})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/welcome.jinja',
                        'subject':'Welcome to Mywash!'})
    logging.info("Sending Welcome Email with data ")
    logging.info(paramDict)
    emailer.sendmailWithTemplate(paramDict = paramDict)
    send_mywash_email(paramDict,subject="New User Joined Alert")

@celery.task
def email_order_placed(data):
    paramDict={}
    senderMail="veera@mywash.com" if data.get("service_type") == "express" else "team@mywash.in"
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':senderMail,
                        'templateName':'templates/emails/order-status0.jinja',
                        'subject':'Your MyWash order #%s is confirmed.' % paramDict['emails']['orderid']})
    logging.info(paramDict)
    print senderMail
    emailer.sendmailWithTemplate(paramDict = paramDict)
    send_mywash_email(paramDict,subject="New Order Alert")

@celery.task
def email_order_pickedup(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/order-status1.jinja',
                        'subject':'You Order is Picked Up'})
    logging.info(paramDict)
    emailer.sendmailWithTemplate(paramDict = paramDict)
    send_mywash_email(paramDict,subject="Order Picked Up Alert")

@celery.task
def email_order_delivered(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/order-status2.jinja',
                        'subject':'You Order is Delivered'})
    logging.info(paramDict)
    emailer.sendmailWithTemplate(paramDict = paramDict)
    send_mywash_email(paramDict,subject="Order Delivered Alert")

@celery.task
def email_order_invoice(data):
    paramDict={}
    paramDict.update(copy.deepcopy(ordersDAO.get_order(data.get("order_id"))))
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/order-status3.jinja',
                        'subject':'Your order Invoice'})

    logging.info(paramDict)
    #print emailer.sendmailWithTemplate(paramDict = paramDict)
    #emailer.sendmailWithTemplate(paramDict = paramDict)
    send_mywash_email(paramDict,subject="Order Invoiced Alert")

@celery.task
def email_order_cancelled(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/order-status5.jinja',
                        'subject':'Your order Invoice'})

    logging.info(paramDict)
    emailer.sendmailWithTemplate(paramDict = paramDict)
    send_mywash_email(paramDict,subject="Order Cancelled Alert")

from twilio.rest import TwilioRestClient
 
account_sid = "AC766c49c31a867f83b8cd649f7607eb4e"
auth_token  = "0eb8257c740796f8f5e4219e3d3abffa"
client = TwilioRestClient(account_sid, auth_token)

@celery.task
def promotion_users():
    all_users=usersDAO.get_all_users()
    if all_users:
        for x in all_users.get("result"):
            paramDict={}
            paramDict.update({'emails':{"user":x.get("first_name","")+" "+x.get("last_name","")}})
            paramDict.update({'recepients':x.get("email"),
                                'recepientName':x.get("first_name","")+" "+x.get("last_name",""),
                                'senderMail':'team@mywash.in',
                                'templateName':'templates/emails/diwali/diwali.jinja',
                                'subject':'Diwali Wishes from Mywash'})

            logging.info(paramDict)
            emailer.sendmailWithTemplate(paramDict = paramDict)

def send_sms(body, to, fromi): 
    message = client.messages.create(body="jujubi on the way",to="08039591212",from_="+12163036707") 
    print message.sid
    return True

"""
This makes a post request to sendgrid api and gets the response 
"""
def unsubscribe(email):
    if request.method == 'GET':
        post_url = 'https://api.sendgrid.com/api/unsubscribes.add.json?method=post&api_user='+app.config['SENDGRID_UNAME']+'&api_key='+app.config['SENDGRID_PWD']+'&email='+email
        response = requests.post(post_url)
        json_data = json.loads(response.text)
        # return json_data['message']
        return render_template('/website/unsubscribe.jinja', message=json_data['message'])
