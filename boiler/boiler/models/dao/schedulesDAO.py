from boiler.models.database import db
from bson.objectid import ObjectId
import pymongo
from bson import json_util
from bson import BSON
from flask import jsonify
import json,copy
import datetime
import logging


def base_schedule():
    return {
        "address_id": 0,
        "user_id": 0,
        "schedule_time": "",
        "schedule_date": "",
        "agent_id": 0,
        "is_active": True,
        "is_pickup": True,
        "created_date": datetime.datetime.now(),
        "updated-date": datetime.datetime.now(),
        "is_completed": True,
    }


def add_schedule(data):
    try:
        logging.info("Adding schedule with data ")
        print data
        schedule_id = db.schedules.insert(data)
    except Exception as e:
        logging.critical("Failed to Insert schedule with exception "+str(e))
        schedule_id = 0
    return schedule_id


def get_schedule(schedule_id):
    try:
        schedules=db.schedules.find_one({"_id":ObjectId(schedule_id)})
        if True:
            schedule=copy.deepcopy(schedules)
            result=copy.deepcopy(schedule)
            for k,v in schedule.items():
                if isinstance(v, ObjectId):
                    result[k] = str(v)
                elif isinstance(v,datetime.date):
                    result[k]=v.strftime("%b %d %Y %H:%M")
            return {"result":[result]}
    except Exception as e:
        logging.critical("Failed to get schedule with exception "+str(e))
    return None


def get_all_schedules():
    try:
        schedules=db.schedules.find()
        json_docs=[]
        for x in schedules:
            json_doc=json.dumps(x,sort_keys=False,indent=4,default=json_util.default)
            json_docs.append(json.loads(json_doc))
        return {"result":json_docs}
    except Exception as e:
        logging.critical("Failed to get all schedules with exception "+str(e))
    return None
