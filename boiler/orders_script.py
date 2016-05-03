from boiler.models.dao import ordersDAO
from boiler.models.database import db
import pymongo
import pprint

import csv


with open('test.csv', 'a') as fp:
    a = csv.writer(fp, delimiter=',')


orders=db.orders.find({}).sort([("created_date",pymongo.DESCENDING)])
for y in orders:
    try:

        x=ordersDAO.get_order_email(str(y.get("_id")))
        data=[]
        try:
            data.append(str(x.get("_id")))
            data.append(str(x.get("user")))
            data.append(str(x.get("status")))
            data.append(str(x.get("type")))
            data.append(str(x.get("phone")))
            data.append(str(x.get("pickup").get("result")[0].get("schedule_date")))
            data.append(str(x.get("pickup").get("result")[0].get("schedule_time")))
            data.append(str(x.get("delivery").get("result")[0].get("schedule_time")))
            data.append(str(x.get("delivery").get("result")[0].get("schedule_time")))
            data.append(str(''.join(str(e) for e in x.get("address",{}).values())))
            with open('test.csv','a') as fp:
                a = csv.writer(fp,delimiter=',')
                a.writerow(data)
            fp.close()
        except Exception as e:
            print str(e)
        
    except Exception as e: 
        print "exception" , str(e)

