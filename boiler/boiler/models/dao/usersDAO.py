from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json
import logging,copy
import datetime
from boiler.models.dao import couponsDAO


def base_user(user_id):   
    if user_exists(user_id):
        #print "user exists for id ",user_id
        return get_user(user_id)
    else:
        now = datetime.datetime.now()
        #print "user doesn't exist for id ",user_id
        return {
                    "user_id":"",
                    "email":"",
                    "name":"Raghu",
                    "pictureUrl":"",
                    "credits":0,
                    "phone":"",
                    "createdAt": now,
                    "updatedAt": now,
                    "authData":{
                        "facebook":{
                            "id":"1067643280",
                            "access_token":"CAAEpRtuEZBOgBAAZBtHiMuf5qnOo4gKHG2vGMybJUZAujSpCgSLu8Ftqlss9Io9XJvuTHmznYZBVTNBopxZAYjUy0LfuRFtWy39IEyTQfDwFFmRAAY184aFQbdPjqYvgkSeUIvT6sWPQDmbnbXBULkHoWNVo4mUaHtf2hZBCZBpJHZCOyGXgAtKZBlJMCGPBMpjbpxTmCWtm3XtOaJh0NWPdTjCeynh9DZCXcZD",
                        }
                    },                               
                }


def update_user(data):
    try:
        data["updatedAt"]=datetime.datetime.now()
        result=db.users.update({'user_id':data.get("user_id")},{'$set':data},upsert=False, multi=False)
        # logging.info(result)
        return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False



def add_user(data):
    try:
        user_id=db.users.insert(data)
        return True
    except Exception as e:
        print "Failed to Insert user with exception ", str(e)
    return False


def get_user(user_id):
    try:
        orders=db.users.find({"user_id":user_id})
        json_docs=[]
        for order in orders:
            #reference https://www.youtube.com/watch?v=vGpdPDKEWdY
            #above reference video helps u understand why we are using deepcopy
            result=copy.deepcopy(order)
            for k,v in order.items():
                #checks if the _id key has ObjectId then only stores the id removing ObjectId. Look into the table data if you have doubt
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                #takes the date and converts into respective format
                elif isinstance(v,datetime.date):
                    result[k]=v.strftime("%b %d %Y %H:%M")
            json_docs.append(result)
        return json_docs[0]
    except Exception as e:
        print "Failed to get user with exception ",str(e)
    return None
    

def get_all_users():
    try:
        orders=db.users.find()
        json_docs=[]
        for order in orders:
            result=copy.deepcopy(order)
            for k,v in order.items():
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                elif isinstance(v,datetime.date):
                    result[k]=v.strftime("%b %d %Y %H:%M")
            json_docs.append(result)
        return {"result":json_docs}     
    except Exception as e:
        print "Failed to get all users with exception ",str(e)
    return None


def user_apply_coupon(coupon_code, user_id):
    try:
        coupon = couponsDAO.get_coupon_by_code(coupon_code)
        user = get_user(user_id)
        if coupon:
            result = db.users.update(
                {'user_id': user_id},
                {'$set': {
                        'credits': coupon.get("amount", 0) + user.get("credits", 0),
                        "updated_date": datetime.datetime.now(),
                        "updatedAt": datetime.datetime.now()
                    }
                },
                upsert=False, multi=False
            )
            # logging.info(result)
            return True
    except Exception as e:
        logging.error("Failed to update order with exception "+str(e))
    return False


def get_name(user_id):
    try:
        orders = db.users.find({"user_id":user_id})
        for order in orders:
            result = copy.deepcopy(order)
            return order.get("name", "")
    except Exception as e:
        print "Failed to get user name with exception ",str(e)
    return " "
    

def user_exists(user_id):
    try:
        orders=db.users.find_one({"user_id":user_id})
        if orders:
            if len(orders)>=1:
                return True      
    except Exception as e:
        print "Failed to find if user exists with exception ",str(e)
    return False

def get_emailByObjId(obj_id):
    try:
        #objOfId = ObjectId(obj_id)
        orders=db.users.find({"_id":ObjectId(obj_id)})
        json_docs=[]
        for order in orders:
            #reference https://www.youtube.com/watch?v=vGpdPDKEWdY
            #above reference video helps u understand why we are using deepcopy
            result=copy.deepcopy(order)
            for k,v in order.items():
                #checks if the _id key has ObjectId then only stores the id removing ObjectId. Look into the table data if you have doubt
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                #takes the date and converts into respective format
                elif isinstance(v,datetime.date):
                    result[k]=v.strftime("%b %d %Y %H:%M")
            json_docs.append(result)
        return json_docs[0]
    except Exception as e:
        print "Failed to get user with exception ",str(e)
    return None


def get_user_by_phone(phone):
    try:
        #objOfId = ObjectId(obj_id)
        users_count = db.users.find({"phone": phone, 'phone_is_valid': True}).count()
        print "users with phone ", phone, " ...count = ", users_count
        return users_count
    except Exception as e:
        print "Failed to get user with exception ", str(e)
    return None


def get_all_users_of_partner(partner_id):
    try:
        print "call made..."
        partner_users = db.users.find({'partner.id': partner_id})
        json_docs = []
        for partner_user in partner_users:
            result = copy.deepcopy(partner_user)
            print "partner_user...", partner_user
            print "partner_user_items....", partner_user.items()
            for k, v in partner_user.items():
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                elif isinstance(v, datetime.date):
                    result[k] = v.strftime("%b %d %Y %H:%M")
            json_docs.append(result)
        print "json_docs", json_docs
        return {"partner_user": json_docs}
    except Exception as e:
        print "Failed to get partner_users with exception ", str(e)
    return None


def get_user_by_order_id(order_id):
    try:
        order = db.orders.find_one({"_id": ObjectId(order_id)})
        print "order......", order
        print "user_id......", order['user_id']
        user_id = order['user_id']

        user = db.users.find_one({"user_id": user_id})
        print "user here......", user
        json_docs = []
        #reference https://www.youtube.com/watch?v=vGpdPDKEWdY
        #above reference video helps u understand why we are using deepcopy
        result = copy.deepcopy(user)
        for k, v in user.items():
            #checks if the _id key has ObjectId then only stores the id removing ObjectId. Look into the table data if you have doubt
            if isinstance(v, ObjectId):
                result[k] = str(v)
            #takes the date and converts into respective format
            elif isinstance(v, datetime.date):
                result[k] = v.strftime("%b %d %Y %H:%M")
        json_docs.append(result)
        return json_docs[0]
    except Exception as e:
        print "Failed to get user with exception ", str(e)
    return None