from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json
#Format of post
#{"title":"First Deal","deal_url":"www.flipkart.com","discount":20,"categories":["fashion","apparel"],"description":"dflka","views":20,"upvotes":0,"price_original":"240Rs","price_current":"220Rs","posted_by":22}

def base_post():   
    return {"title":"","deal_url":"","discount":0,"categories":[],"description":"","views":0,"upvotes":0,"price_original":"","price_current":"","posted_by":0}


def get_top(count):
    posts=db.posts.find().sort([("upvotes",pymongo.DESCENDING)])
    json_docs=[]
    for x in posts:            
        json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
        json_docs.append(json.loads(json_doc))
    return {"result":json_docs}

def add_post(data):
    posts=db.posts
    posts.insert(data)
    return True    

def get_post(post_id):
    post=db.posts.find_one({'_id':ObjectId(post_id)})
    return post


def get_trending(count):   
    posts=db.posts.find().sort([("upvotes",pymongo.DESCENDING)])
    json_docs=[]
    for x in posts:            
        json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
        json_docs.append(json.loads(json_doc))
    return {"result":json_docs}
