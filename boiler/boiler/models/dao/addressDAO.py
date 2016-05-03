from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json,copy
import datetime,logging


def base_address():
    return {
        "user_id":"",
        "address_1":"SFS 407, Yelahanka New Town,",
        "tag":"",
        "address_2":"SFS 407, Yelahanka New Town,",
        "state":"karnataka",
        "city":"bangalore",
        "apartment_number":"",
        "pincode":0,
        "is_active":True,
        "latitude":37.8020405,
        "longitude":-122.4382307,
    }


def add_address(data):
    try:
        print "Adding address with data",data
        address_id=db.addresses.insert(data)
        address_id=str(address_id)
    except Exception as e:
        logging.critical("Failed to Insert address with exception "+str(e))
        address_id=0
    return address_id


def remove_address(object_id):

    try:
        print db.addresses.find_and_modify(
            query={'_id': ObjectId(object_id)}, update={"$set": {'is_active': False}},
            upsert=False, full_response= True)
        return True
    except Exception as e:
        logging.critical("Failed to delete address with exception "+str(e))
        return False

def update_address(data, object_id):
    try:
        address_update = db.addresses.update(
                                    {'_id':ObjectId(object_id)},
                                    {'$set':data},upsert=False, multi=False)
        print address_update
        return True

    except Exception as e:
        logging.critical("Failed to update address with exception "+str(e))
        return False



def get_address(address_id):
    try:
        addresses=db.addresses.find_one({"_id":ObjectId(address_id)})
        address=copy.deepcopy(addresses)
        result=copy.deepcopy(address)
        for k,v in address.items():
            if isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v,datetime.date):
                result[k]=v.strftime("%b %d %Y %H:%M")

        return {"result":[result]}
    except Exception as e:
        logging.critical("Failed to get address with exception "+str(e))
    return None

def get_user_address(user_id):
    try:
        print "Getting User Addresses for User ID",user_id
        orders=db.addresses.find({'user_id':user_id, "is_active": True})
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
        logging.critical("Failed to get all addresses with exception "+str(e))
    return None



def get_all_addresss():
    try:
        orders=db.addresses.find()
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
        logging.critical("Failed to get all addresses with exception "+str(e))
    return None