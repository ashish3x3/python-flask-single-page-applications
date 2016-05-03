from flask import request, session, jsonify, redirect, json
from boiler.renderer import commonrender
from boiler.models.dao import usersDAO, addressDAO
import copy, logging
from datetime import datetime

def subscribe_email():
    email=request.args.get("email")

    post_id = 0 # SubscribersDAO.add_email_subscriber(email)
    if post_id >0:
        result={"status": 204, "body": {"status": True, "post":{"id":0}}}
    else:
        result={"status": 204, "body": {"status": False, "message": "Failed to post"}}
    return jsonify(result)
    """
    userid=None
    result=usersDAO.add_subscription(userid,email)
    return True"""




@commonrender('profile/myprofile.jinja')
def user_profile():
    result = copy.deepcopy(session.get("header",{}))
    if session.get('id',''):
        result.update(usersDAO.get_user(session.get("id","")))
        address_list = addressDAO.get_user_address(session.get("id","")).get("result")
        result.update({"address_list":dict(enumerate(address_list))})
        # logging.info(result)
        return result
    else:
        return redirect('/order_schedule')

def edit_profile():
    result = copy.deepcopy(session.get('header', {}))
    if request.method == 'POST':
        try:
            print 'result before', usersDAO.get_user(session.get('id',''))
            copy_data = copy.deepcopy(request.form)
            update_result = usersDAO.update_user({
                "name": copy_data.get("name", ""),
            })
            if update_result:
                result.update(usersDAO.get_user(session.get('id','')))
                return jsonify(result)
        except Exception, e:
            return jsonify({'data': {'status': 'failure', 'error': 'db error'}}), 500

