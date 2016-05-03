from boiler.models.dao import ordersDAO
from flask import jsonify,request,session,render_template

import Constants

import datetime,copy


def submit_order():
    try:
        if request.method=='order':
            data={}

            copy_data=copy.deepcopy(request.form)
            for x in copy_data.keys():
                try:
                    data.update({x:copy_data[x]})
                except Exception as e:
                    pass
            try:
                data.update({"ordered_on":datetime.datetime.now()})
                data.update({"upvotes":0})
                data.update({"views":0})
                data.update({"comments":{"count":0}})
                data.update({"ordered_by":{"name":session['header']['user']['name'],"profile_pic":session['header']['user']['pictureUrl']}})
            except Exception as e:
                print "Failed to populate data while ordering deal",str(e)
        order_id=ordersDAO.submit_order(data)
    except Exception,e:
        print str(e)
        order_id=0
    if order_id >0:
        result={"status": 204, "body": {"status": True, "order":{"id":0}}}
    else:   
        result={"status": 204, "body": {"status": False, "message": "Failed to order"}}
    return jsonify(result)


def get_top():
    result_set=ordersDAO.get_top(Constants.PAGE_SIZE)
    return jsonify(result_set)


def upvote():
    order_id=request.args.get("order_id",0)
    result=ordersDAO.upvote_order(session["id"],order_id)
    
    if result >0:
        result={"status": 204, "body": {"status": True, "order":{"id":0}}}
    else:   
        result={"status": 204, "body": {"status": False, "message": "Failed to order"}}
    return jsonify(result)


def get_order(order_id):
    
    result=ordersDAO.get_order(order_id)
    return True


def trending():
    count = request.args.get("count",5)
    result=ordersDAO.get_trending(count)
    return result
