import datetime
from flask import render_template,session, make_response, request, jsonify, json
from boiler.models.dao import itemsDAO
from boiler.models.dao import ordersDAO
from boiler.models.dao import usersDAO
from boiler.renderer import commonrender
import copy,logging
from pprint import pprint
import requests
from boiler.celery_app.celeryconfig import celery
import copy

sid = 'mywash'
token = 'c8bed8711ba94667d385418a6d3705828bb7884a'

@celery.task
def send_message(sid, token, sms_from, sms_to, sms_body):
    return requests.post('https://twilix.exotel.in/v1/Accounts/{sid}/Sms/send.json'.format(sid=sid),
        auth=(sid, token),
        data={
            'From': sms_from,
            'To': sms_to,
            'Body': sms_body
        })


def mywash_order_transactional_sms(phone,text):
    r=send_message(sid,token,sms_from="mywash",sms_to=phone,sms_body=text)
    print r.status_code
    pprint(r.json())

def mywash_internal_sms(sms_body):  
    return
    r=send_message(sid,token,sms_from="mywash",sms_to="7411721439",sms_body=sms_body)
    print r.status_code
    pprint(r.json())


@celery.task
def sms_welcome():
    print "We don't  have sms for welcome"
    """
    paramDict={}
    paramDict.update({'emails': {'user':data.get("name"," ")}})
    paramDict.update({'recepients':data.get("email"),
                        'recepientName':data.get("name"),
                        'senderMail':'team@mywash.in',
                        'templateName':'templates/emails/welcome.jinja',
                        'subject':'Welcome to Mywash.in'})
    logging.info("Sending Welcome SMS with data ")
    logging.info(paramDict)
    mywash_order_transactional_sms(paramDict)
    mywash_internal_sms("New User Joined Alert")
    """

@celery.task
def sms_order_placed(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})    
    logging.info("Sending Order SMS with data ")
    logging.info(paramDict)
    text="Hi "+data.get('name',"user") +" ,we have received your order. Mywash agent will be there between "+ paramDict["emails"].get("pickup")["result"][0].get("schedule_time") +" on "+ paramDict["emails"].get("pickup")["result"][0].get("schedule_date") +" for the pickup."
    mywash_order_transactional_sms(paramDict["emails"].get("phone"),text)
    #mywash_internal_sms("New Order Alert ")
    
@celery.task
def sms_alert_agent_pickup(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})
    text="Hi "+data.get('name',"user") +", mywash agent is on the way for the pickup between "+paramDict["emails"].get("pickup")["result"][0].get("schedule_time")+". Reach us at 08039591212 for queries."
    logging.info("Sending agent pickup alert for ")
    logging.info(data)
    mywash_order_transactional_sms(data.get("phone"),text)

@celery.task
def sms_order_pickedup(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})    
    logging.info(paramDict)
    mywash_order_transactional_sms(paramDict)
    mywash_internal_sms("Order Picked Up Alert")

@celery.task
def sms_order_delivered(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})    
    mywash_order_transactional_sms(paramDict)
    mywash_internal_sms("Order Delivered Alert")

@celery.task
def sms_order_invoice(data):
    paramDict={}
    paramDict.update(copy.deepcopy(ordersDAO.get_order(data.get("order_id"))))    

    logging.info(paramDict)
    #print emailer.sendmailWithTemplate(paramDict = paramDict)
    mywash_order_transactional_sms(paramDict)
    mywash_internal_sms("Order Invoiced Alert")

@celery.task
def sms_order_cancelled(data):
    paramDict={}
    paramDict.update({'emails':copy.deepcopy(ordersDAO.get_order_email(data.get("order_id")))})    
    logging.info(paramDict)
    text="Hi "+data.get("name","user")+", your order has been cancelled. We hope to serve you sometime soon. Click this link to http://bit.ly/1wKC6tj place a new order."
    mywash_order_transactional_sms(paramDict["emails"].get("phone"),text)
    mywash_internal_sms("Order Cancelled Alert")





