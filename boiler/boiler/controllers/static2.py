import datetime
from flask import render_template,session, make_response, request, jsonify, json
from boiler.models.dao import itemsDAO
from boiler.renderer import commonrender
import copy
from flask import Flask, make_response
import sms
from boiler.models.dao import ordersDAO
from boiler.models.database import db
import pymongo
import csv
from datetime import datetime, date
from bson.objectid import ObjectId
import Constants

def get_report():
    d1 = datetime.now()
    schedules = {str(schedule['_id']): schedule for schedule in db.schedules.find()}
    orders = list(db.orders.find({}).sort([("created_date",pymongo.DESCENDING)]))
    addresses = {str(address['_id']): address for address in db.addresses.find()}
    users = {str(user['user_id']): user for user in db.users.find()}

    with open('test.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        for order in orders:
            try:
                data = []
                result = {}
                for k, v in order.items():
                    if isinstance(v, date):
                        result[k] = v.strftime("%b %d %Y %H:%M")
                try:
                    data.append(str(order.get("_id")))
                    data.append(users[str(order.get("user_id"))].get('name', ''))
                    data.append(users[str(order.get("user_id"))].get('email', ''))
                    data.append(str(Constants.ORDER_DICT.get(str(order.get("status")),"")))
                    data.append(str(order.get("type")))
                    data.append(str(order.get("phone"))) 
                    data.append(str(schedules[str(order.get("pickup_id"))].get("schedule_date")))
                    data.append(str(schedules[str(order.get("pickup_id"))].get("schedule_time")))
                    data.append(str(schedules[str(order.get("delivery_id"))].get("schedule_date")))
                    data.append(str(schedules[str(order.get("delivery_id"))].get("schedule_time")))
                    data.append(str(''.join(str(e) for e in addresses.get(str(order.get("address_id")), {}).values())))
                    a.writerow(data)
                except Exception as e:
                    print e
            
            except Exception as e: 
                print "exception" , str(e)

    delta = datetime.now() - d1
    # print delta.microseconds, delta.seconds

    # Check for valid file and assign it to `inbound_file`
    inbound_file=open("test.csv","r")
    data = inbound_file.read()
    response = make_response(data)
    response.headers["Content-Disposition"] = "attachment; filename=test.csv"
    return response


