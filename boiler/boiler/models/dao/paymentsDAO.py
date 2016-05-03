from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json
import datetime


#Format of post
#{"title":"First Deal","deal_url":"www.flipkart.com","discount":20,"categories":["fashion","apparel"],"description":"dflka","views":20,"upvotes":0,"price_original":"240Rs","price_current":"220Rs","posted_by":22}

def base_category():   
    return {"title":"","deal_url":"","discount":0,"categories":[],"description":"","views":0,"upvotes":0,"price_original":"","price_current":"","posted_by":0}



def add_category(data):
    categories=db.categories
    categories.insert(data)
    return True    

def get_all_categories(limit):
    try:
        categories=db.categories.find().sort([("deals_count",pymongo.DESCENDING)])
        json_docs=[]
        for x in categories:            
            json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
            json_docs.append(json.loads(json_doc))
        return {"result":json_docs}
    except Exception as e:
        print "Failed to get categories with exception ",str(e)

    return None
    



