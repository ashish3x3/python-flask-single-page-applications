from pymongo import MongoClient
from boiler import config

client = MongoClient("mongodb://" + config.MONGO_CREDS['HOST'] + ":" + config.MONGO_CREDS['PORT'])
db = client.dealsup
logger = client.mywash_logs
