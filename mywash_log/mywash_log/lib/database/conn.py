import pymongo
import redis

def mongo(conf):
    return pymongo.MongoClient("mongodb://" + conf['HOST'] + ":" + conf['PORT'])

def redis_conn(conf):
    return redis.Redis(host=conf['HOST'], port=conf['PORT'], db=conf['DB'])