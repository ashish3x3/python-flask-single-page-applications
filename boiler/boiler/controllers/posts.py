from boiler.models.dao import postsDAO
from flask import jsonify,request,session,render_template
import datetime,copy

def submit_post():
    try:
        if request.method=='POST':
            data={}
            print request.form

            copy_data=copy.deepcopy(request.form)
            for x in copy_data.keys():
                print x
                try:
                    data.update({x:copy_data[x]})
                except Exception as e:
                    pass
            try:
                data.update({"posted_on":datetime.datetime.now()})
                data.update({"upvotes":0})
                data.update({"views":0})
                data.update({"comments":{"count":0}})
                data.update({"posted_by":{"name":session['header']['user']['name'],"profile_pic":session['header']['user']['pictureUrl']}})
            except Exception as e:
                print "Failed to populate data while posting deal",str(e)
        post_id=postsDAO.submit_post(data)
    except Exception,e:
        print str(e)
        post_id=0
    if post_id >0:
        result={"status": 204, "body": {"status": True, "post":{"id":0}}}
    else:   
        result={"status": 204, "body": {"status": False, "message": "Failed to post"}}
    return jsonify(result)


def get_top(count):
    result_set=postsDAO.get_top(count)
    return jsonify(result_set)


def upvote():
    post_id=request.args.get("post_id",0)
    result=postsDAO.upvote_post(session["id"],post_id)
    
    if result >0:
        result={"status": 204, "body": {"status": True, "post":{"id":0}}}
    else:   
        result={"status": 204, "body": {"status": False, "message": "Failed to post"}}
    return jsonify(result)


def get_post(post_id):
    
    result=postsDAO.get_post(post_id)
    return True


def trending():
    count = request.args.get("count",5)
    result=postsDAO.get_trending(count)
    return result
