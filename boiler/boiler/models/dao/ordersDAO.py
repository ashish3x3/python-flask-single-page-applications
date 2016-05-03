from boiler import config
from boiler.models.database import db
from boiler.models.dao import schedulesDAO
from boiler.models.dao import addressDAO
from boiler.models.dao import usersDAO
from bson.objectid import ObjectId
from boiler import app
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json,copy
import datetime
import Constants,logging
from bson.json_util import dumps
import random, requests
import pprint

char_collection = range(48, 58)
char_collection2 = range(65, 91) + range(48, 58)
hash_num = len(char_collection)


def uniqueOrderId():
    datepart_list = datetime.datetime.utcnow().strftime("%y-%m-%d").split("-")
    datepart = chr(char_collection2[int(datepart_list[0])-1]) \
     + chr(char_collection2[int(datepart_list[1])-1]) \
     + chr(char_collection2[int(datepart_list[2])-1])
    shift = random.randint(0, 9)
    last_part = ""
    for i in range(0, 5):
        selection = random.randint(0, hash_num-1)
        index = (selection + shift) % hash_num
        last_part += chr(char_collection[index])
    order_id = datepart + last_part
    if db.orders.find({'order_id': order_id}).count():
        return uniqueOrderId()
    else:
        return order_id

#Format of order
#{"title":"First Deal","deal_url":"www.flipkart.com","discount":20,"categories":["fashion","apparel"],"description":"dflka","views":20,"upvotes":0,"price_original":"240Rs","price_current":"220Rs","ordered_by":22}

def base_order():
    data = {
        "user_id": "",
        "address_id": "",
        "status": "order_placed",
        "rating": None,
        "special_instructions": "",
        "payment_id": "",
        "pickup_id": 0,
        "delivery_id": 0,
        "order_price": 0,
        'coupon': {},
        "final_price": 0,
        'last_credit_used': 0,
        "credits_applied": 0,
        "order_items": {},
        "agent_verified_items": False,
        "phone": "",
        "type": "",
        "created_date": datetime.datetime.now(),
        "updated_date": datetime.datetime.now(),
        "order_id": uniqueOrderId()
    }
    return data



def add_items(order_id,data):
    try:        
        data.update({"updated_date":datetime.datetime.now()})
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':data},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to add rating for order with exception "+str(e))
    return False

def add_rating(order_id,rating):
    try:
        data={"rating":rating}
        data.update({"updated_date":datetime.datetime.now()})
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':data},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to add rating for order with exception "+str(e))
    return False

def update_order(order_id,data):
    try:
        data.update({"updated_date":datetime.datetime.now()})
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':data},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False

def order_delivered(order_id,schedule_id):
    try:
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':{'delivery_id':schedule_id,"updated_date":datetime.datetime.now()}},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False


def order_picked_up(order_id,schedule_id):
    try:
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':{'pickup_id':schedule_id,"updated_date":datetime.datetime.now()}},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False


def order_status_update(order_id,status):
    try:
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':{'status':status,"updated_date":datetime.datetime.now()}},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False

def order_update_feedback(order_id,rating):
    try:
        result=db.orders.update({'_id':ObjectId(order_id)},{'$set':{'rating':rating,"updated_date":datetime.datetime.now()}},upsert=False, multi=False)
        logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False

def apply_coupon(order_id,amount):
    try:
        order=get_order(order_id)
        if order:
            result=db.orders.update({'_id':ObjectId(order_id)},{'$set':{'final_price':order.get("order_price")-amount,"updated_date":datetime.datetime.now()}},upsert=False, multi=False)
            logging.info(result)
            return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False


def submit_order(data):
    try:
        order_id=db.orders.insert(data)
        order_id=str(order_id)
    except Exception as e:
        logging.critical("Failed to order with exception: "+str(e))
        order_id=None
    return order_id


def get_order(order_id):
    orders = None
    try:
        if len(order_id) < 15:
            orders=db.orders.find({'order_id':order_id})
        else:
            orders=db.orders.find({'_id':ObjectId(order_id)})
        order=copy.deepcopy(orders[0])
        result=copy.deepcopy(order)
        for k,v in order.items():
            if isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v,datetime.date):
                result[k]=v.strftime("%b %d %Y %H:%M")

        if result:
            try:
                result.update({"delivery":copy.deepcopy(schedulesDAO.get_schedule(str(order.get("delivery_id"))))})
                result.update({"pickup":copy.deepcopy(schedulesDAO.get_schedule(str(order.get("pickup_id"))))})
                result.update({"address":copy.deepcopy(addressDAO.get_address(str(order.get("address_id"))))})
            except Exception as e:
                print "Failed to get order email with exception " ,str(e)
        return result
    except Exception as e:
        print "Failed to Fetch order with exception ",str(e)
    return None


# def get_top_orders(count,user_id):
def get_top_orders(user_id):
    if user_id:
        orders = requests.get(app.config['API_SERVER']['private_dashboard'] + '/api/orderhistory/' + user_id).json()['data']
        json_docs = []
        for order in orders:
            result = copy.deepcopy(order)
            for k, v in order.items():
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                elif isinstance(v, datetime.date):
                    result[k] = v.strftime("%b %d %Y %H:%M")
            json_docs.append(result)
        return {"result": json_docs}
    else:
        return None


def get_pending_order_id(user_id):
    orders=db.orders.find({'user_id':user_id}).sort([("updated_date",pymongo.DESCENDING)])
    json_docs=[]
    for x in orders:
        if x.status < 4:
            return str(x.get("_id"))
    return None



def get_order_email(order_id):
    try:
        orders=db.orders.find({'_id':ObjectId(order_id)})

        order=copy.deepcopy(orders[0])
        users = usersDAO.get_user(order.get('user_id'))
        result=copy.deepcopy(order)
        for k,v in order.items():
            if isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v,datetime.date):
                result[k]=v.strftime("%b %d %Y %H:%M")
        if result:
            washtypes = order.get('type')
            washtype_str = ""
            if isinstance(washtypes, list):
                washtype_str = ', '.join([Constants.TYPE_DICT[wash] for wash in washtypes])
            else:
                washtype_str = washtypes
            try:
                result.update({"delivery":copy.deepcopy(schedulesDAO.get_schedule(str(order.get("delivery_id"))))})
                result.update({"pickup":copy.deepcopy(schedulesDAO.get_schedule(str(order.get("pickup_id"))))})
                result.update({"address":copy.deepcopy(addressDAO.get_address(str(order.get("address_id")))["result"][0])})
                result.update({"user":copy.deepcopy(users.get('name', ' ').split(' ')[0])})
                result.update({"phone":copy.deepcopy(users.get('phone'))})
                result.update({"type": washtype_str})
                result.update({"status":Constants.ORDER_DICT.get(str(order.get("status")),"")})
                result.update({"orderid":order['order_id']})
                result.update({"pickup_address":copy.deepcopy(addressDAO.get_address(str(order.get("address_id"))))})
                result.update({"clothes":copy.deepcopy(dict(enumerate(order.get("order_items"))))})
                result.update({"ordervalue":order.get("order_price")})
                result.update({"credits":order.get("credits_applied")})
                result.update({"totalpayable":order.get("order_price",0)-order.get("credits_applied",0)})
            except Exception as e:
                print "Failed to get order email with exception " ,str(e)
        return result
    except Exception as e:
        print "Failed to Fetch order with exception ",str(e)
    return None
