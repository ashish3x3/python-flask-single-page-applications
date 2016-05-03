from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json,copy
import datetime



def base_item():   
    return {
            "title":"Wash and Fold",
            "price":{"laundry":1.3,"dry_cleaning":3.3},
            "imageUrl":"https://www.filepicker.io/api/file/VJKBa07wT4O92VNWUwRi",
            "is_per_kg":False,
            "is_visible_to_customer":True,
            "isActive":True,
            "category":"Household",
        }


def add_item(data):
    try:
        print data
        item_id=db.items.insert(data)
    except Exception as e:
        print "Failed to Insert item with exception ", str(e)
        item_id=0
    return item_id


def get_item(item_id):
    try:
        orders=db.items.find({"_id":int(float(item_id))})
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
        print "Failed to get item with exception ",str(e)
    return None
    



def get_all_items():
    try:
        orders=db.items.find().sort([("_id",pymongo.ASCENDING)])
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
        print "Failed to get all items with exception ",str(e)
    return None
