from flask import request,session,jsonify,redirect
from boiler.models.dao import usersDAO
from boiler.models.dao import subscribersDAO
import copy,logging
from boiler.renderer import commonrender


def apply_coupon():
    result=copy.deepcopy(session.get("header",{}))
    if request.method=='POST':
        coupon_code=request.form.get("coupon_code","")
    else:
        coupon_code=request.args.get("coupon_code")

    message={}
    message["msg"]="Failed to apply coupon"

    user=usersDAO.get_user(session.get("id"))


    if coupon_code=="wash200":
        result1=None
        message["msg"]="Coupon Expired.Contact us for new coupons"
    elif user.get("credits")>10:
        result1=None
        message["msg"]="Only one coupon is accepted"
    else:   
        result1=usersDAO.user_apply_coupon(coupon_code,session.get("id"))
   
    if result1:
        session["header"]["user"]["credits"]=usersDAO.get_user(session.get("id")).get("credits",0)
        session.modified = True
        result.update({"status": 204, "body": {"status": True}})
    else:  
        result.update({"status": 204, "body": {"status": False, "message": message.get("msg")}})
        print "unable to apply coupon succesfully ",coupon_code,session.get("id")
    return jsonify(result)


def validate_coupon(order_id):
    if not order_id:
        return {"status": "failure", "error": "order_id absent."}, 400



#commonrender is a decorator function in renderer.py
@commonrender('coupons/form.jinja')
def coupon_form():
    result = copy.deepcopy(session.get("header", {}))
    result.update()
    return result



@commonrender('refer/form.jinja')
def refer_form():
    result=copy.deepcopy(session.get("header",{}))
    return result



@commonrender('ratings/form.jinja')
def ratings():
    result=copy.deepcopy(session.get("header",{}))
    return result





@commonrender('help/form.jinja')
def help():
    result=copy.deepcopy(session.get("header",{}))
    return result




@commonrender('help/faq.jinja')
def faq():
    result=copy.deepcopy(session.get("header",{}))
    return result


@commonrender('website/terms.jinja')
def terms():
    result=copy.deepcopy(session.get("header",{}))
    return result



@commonrender('coupons/privacy.jinja')
def privacy():
    result=copy.deepcopy(session.get("header",{}))
    return result

def section():
    return redirect('/terms#express')
