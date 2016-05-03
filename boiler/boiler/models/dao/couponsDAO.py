from boiler.models.database import db
from bson.objectid import ObjectId
from bson import json_util
import json
import datetime
import logging


def base_coupon():   
    return {
                "code": "",
                "valid_from": "",
                "valid_to": datetime.datetime.now()+datetime.timedelta(days=10),
                "is_percent": True,
                "amount": 0,
                "count": 0,
                "description": "",
                "count_available": 0,
                "created_date": "",
                "updated_date": "",
                "is_active": False
            }


def add_coupon(data):
    try:
        coupon_id=db.coupons.insert(data)
    except Exception as e:
        print "Failed to Insert Coupon with exception ", str(e)
        coupon_id=0
    return coupon_id


def coupon_checker(coupon_id):
    try:
        flag=True
        coupon_object=get_coupon_by_id(coupon_id)
        if coupon_object:
            if datetime.datetime.now()>coupon_object.get("valid_to"):
                flag=False
            if coupon_object.get("count_available")<1:
                flag=False
        else:
            flag=False
    except Exception as e:
        logging.critical("Failed to check coupon code with exception"+str(e))
    
    return flag


def get_coupon_by_code(coupon_code):
    try:
        coupons=db.coupons.find({"code":coupon_code})
        json_docs=[]
        for x in coupons:            
            json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
            json_docs.append(json.loads(json_doc))
        if len(json_docs)>0:
            return json_docs[0]
    except Exception as e:
        print "Failed to get coupon with exception ",str(e)
    return None
    

def get_coupon_by_id(coupon_id):
    try:
        coupons=db.coupons.find({"_id":ObjectId(coupon_id)})
        json_docs=[]
        for x in coupons:            
            json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
            json_docs.append(json.loads(json_doc))
        
        if len(json_docs)>0:
            return json_docs[0]
    except Exception as e:
        print "Failed to get coupon with exception ",str(e)
    return None


def use_coupon(coupon_code):
    try:
        coupon=get_coupon_by_code(coupon_code)
        coupon_id=coupon.get("_id",0)
        if coupon:
            result=db.coupons.update({'_id':coupon_id.get("$oid","")},{'$set':{'count_available':coupon.get("count_available")-1,"updated_date":datetime.datetime.now()}},upsert=False, multi=False)
            logging.info(result)
            return True
    except Exception as e:
        logging.error("Failed to Update Coupon Usage with exception "+str(e))
    return False


