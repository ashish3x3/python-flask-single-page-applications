from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json
import datetime


def add_email_subscriber(email):
    try:
        data={}
        store_data={}
        data.update({"email":email})
        data.update({"channel":"email"})
        data.update({"emails_sent":0})
        data.update({"joined_date":datetime.datetime.now()})
        store_data["email"]=data
        post_id=db.subscribers.insert(store_data)
    except Exception as e:
        print "Failed to add email subscribers with exception ", str(e)
        post_id=0
    return post_id

def get_subscribers(count):
    posts=db.subscribers.find()
    json_docs=[]
    for x in posts:            
        json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
        json_docs.append(json.loads(json_doc))
    return {"result":json_docs}