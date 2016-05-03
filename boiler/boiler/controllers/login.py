from flask.ext.login import login_user, logout_user, current_user, login_required
#import boiler.service.fb
from flask import session,request,jsonify,redirect,g,url_for,make_response,render_template,redirect
import user
import logging,copy
from boiler.models.dao import usersDAO
from boiler.models.dao import ordersDAO
import json,random,string,httplib2
import requests,Constants
from boiler.renderer import commonrender
import emails
from boiler import app
from boiler import config
from datetime import datetime
import os


def login():
    return True


def fb_login():
    access_token = request.args.get("access_token")
    if access_token:
        session["access_token"] = access_token
        get_me_fb_data()
        
        try:
            response = extendToken(access_token)
            """
            if 'access_token' in response:
                access_token = response.get("access_token")
                logging.info('old access_token : '+str(tmp_access_token))
                logging.info('new access_token : '+str(access_token))
            else:
                logging.error('No extended access_token found')
            session["access_token"] = access_token
            """
        except Exception as e:
            print "Failed to extend access_token with Exception :", str(e)
    return redirect('/verifyphone')


def extendToken(access_token=False):
        """
        if not access_token:
            access_token = session["access_token"]

        g = facebook.GraphAPI(access_token)
        response = graph.extend_access_token(app.config["APP_ID"],app.config["APP_SECRET"])
        return response"""
        return []


def get_me_fb_data():
    try:
        payload = {"access_token": session["access_token"], "fields": "id,name,picture,email"}
        response = requests.get("https://graph.facebook.com/me", 
            params=payload)
        response_json = response.json()
        session["me"] = response_json
        session["id"] = "fb_" + response_json.get("id")
        session['header'] = {'user': {"name": "", "pictureUrl": "", "id": ""}}
        base_user_data = usersDAO.base_user(session.get("id"))

        insert_data = {}
        try:
            session['header']['user']['pictureUrl'] = response_json.get(
                "picture", {"data": ""}).get("data").get("url")
            insert_data["pictureUrl"] = response_json.get(
                "picture", {"data": ""}).get("data").get("url")
        except Exception as e:
            session['header']['user']['pictureUrl'] = Constants.GRAPH_URL + str(response.json().get("id")) + Constants.FB_PICTURE_URL
            insert_data["pictureUrl"] = Constants.GRAPH_URL + str(
                response.json().get("id")) + Constants.FB_PICTURE_URL
            print "Failed to get pictureUrl from fb with exception : ", str(e)
        session['header']['user']['id'] = response_json.get("id")
        session['header']['user']["name"] = response_json.get("name", "")
        session["header"]["user"]["type"] = "fb"
        session["header"]["user"]["email"] = response_json.get("email")
        session["type"] = Constants.FACEBOOK_USER
        session["header"]["user"]["credits"] = base_user_data.get("credits", 0)
        session["header"]["user"]["phone"] = base_user_data.get("phone", 0)

        session["phone_is_valid"] = base_user_data.get("phone_is_valid", False)
        print 'base user --> ', base_user_data
        
        insert_data["user_id"] = session.get("id")
        insert_data["name"] = response_json.get("name", "")        
        insert_data["email"] = response_json.get("email")
        insert_data["updatedAt"] = base_user_data.get('updatedAt', datetime.now())
        insert_data["authData"] = copy.deepcopy(session.get("header")["user"])
        insert_data["authData"]["access_token"] = session.get("access_token")
        insert_data['headers'] = {'user_agent': request.headers.get('User-Agent', '')}
        
        if usersDAO.user_exists(insert_data.get("user_id")):
            usersDAO.update_user(insert_data)
        else:
            insert_data["createdAt"] = base_user_data.get('createdAt', datetime.now())
            usersDAO.add_user(insert_data)
            emails.email_welcome({
                "email": insert_data["email"], "name": insert_data["name"]})

    except Exception as e:
        print "Failed to set me data in session with exception : ",str(e)


def google_login():
    access_token = request.args.get("access_token")
    if access_token:
        session["access_token"] = access_token
        get_me_google_data()

    return redirect('/verifyphone')


def get_me_google_data():
    try:
        payload = {"access_token": session["access_token"]}
        response = requests.get("https://www.googleapis.com/plus/v1/people/me"
            , params=payload)
        session["me"] = response.json()
        # The below line has to be changed to put the db id
        response_data = response.json()
        session["id"] = "g_" + response_data.get("id")
        session['header'] = {'user': {"name": "", "pictureUrl": "", "id": "", 
            }}
        session['header']['user']['pictureUrl'] = response_data.get(
            "image", {"url": ""}).get("url")
        session['header']['user']['id'] = response_data.get("id")
        session['header']['user']["name"] = response_data.get("name", "").get(
            "givenName", "") + " " + response_data.get("name", "").get(
            "familyName", "")
        session["header"]["user"]["type"] = "google"
        session["header"]["user"]["email"] = response_data.get("emails")[0].get("value","")
        session["type"] = Constants.GOOGLE_USER
        base_user_data = usersDAO.base_user(session.get("id"))
        session["header"]["user"]["credits"] = base_user_data.get("credits", 0)
        session["header"]["user"]["phone"] = base_user_data.get("phone", 0)

        session["phone_is_valid"] = base_user_data.get("phone_is_valid", False)
        print 'base user --> ', base_user_data
        insert_data = {}
        insert_data["pictureUrl"] = response_data.get("image", {"url": ""}).get("url")
        insert_data["user_id"] = session.get("id")
        insert_data["name"] = response_data.get("name", "").get("givenName", "")+" "+response_data.get("name","").get("familyName","")
        try:
            insert_data["email"] = response_data.get("emails")[0].get("value","")
        except Exception,e:
            pass
        insert_data["authData"] = copy.deepcopy(session.get("header")["user"])
        insert_data["authData"]["access_token"] = session.get("access_token")
        insert_data['headers'] = {'user_agent': request.headers.get('User-Agent', '')}
        insert_data["updatedAt"] = base_user_data.get('updatedAt', datetime.now())

        if usersDAO.user_exists(insert_data.get("user_id")):
            usersDAO.update_user(insert_data)
        else:
            insert_data["createdAt"] = base_user_data.get('createdAt', datetime.now())
            usersDAO.add_user(insert_data)
            emails.email_welcome({"email":insert_data["email"],"name":insert_data["name"]})

    except Exception as e:
        print "Failed to set me data in session with exception : ",str(e)

@commonrender('website/index.jinja')
def landing():
    #This will put the user block in place
    #print "SESSION HEADER ->",session.getsession("header",{})
    result = copy.deepcopy(session.get("header",{}))
    return result    

@commonrender('website/maintainence_index.jinja')
def maintainence_landing(somepath=None):
    result = copy.deepcopy(session.get("header",{}))
    return result    


@commonrender('website/about.jinja')
def about():
    #This will put the user block in place
    result = copy.deepcopy(session.get("header",{}))
    return result


#aboutus is not referring to any page so removed it
def twitter_login():
    #Implement the twitter login for twitter    
    return redirect(decision())


def verify_phone():
    if session.get('phone_is_valid', ''):
        return redirect(decision())
    else:
        result = copy.deepcopy(session.get("header", {}))
        if session.get('id', ''):
            resp = make_response(render_template('login/verifyphone.jinja', **result))
            print session
            return resp
        else:
            return redirect("/login")


def validate_phone_otp():
    if session.get('phone_is_valid', ''):
        return redirect(decision())
    else:
        result = copy.deepcopy(session.get("header", {}))
        copy_data = copy.deepcopy(request.form)
        print "form data ", request.form
        if session.get('id', ''):
            if 'phone_num' in copy_data:
                phone = copy_data['phone_num']
                print "phone number :-->", phone
                print session
                if not (len(phone) == 10 and phone.isdigit()):
                    result.update({'status': 204, "body": {
                        'status': False, 'message': 'Phone number is invalid. Must be 10 digits only.'}})
                    return jsonify(result)

                count_users = usersDAO.get_user_by_phone(phone)
                if(count_users >= 1):
                    result.update({'status': 204, "body": {
                        'status': False, 'message': 'Phone Number already exists'}})
                    return jsonify(result)

                url = config.API_SERVER['private_dashboard'] + "/api/user/verifyphone"
                r = requests.post(url, data={'phone': phone, 'user_id': session.get("id",'')})
                phone_verify_data = r.json()
                session['otp'] = phone_verify_data['otp']
                session['phone'] = phone
                result.update({'status': 204, "body": {
                        'status': True, 'message': 'phone', 'phone_num': phone}})
            elif 'otp' in copy_data:
                form_otp = copy_data['otp']
                if not (len(form_otp) == 5 and form_otp.isdigit()):
                    result.update({'status': 204, "body": {'status': False, 'message': 'The key you entered is invalid.'}})
                    return jsonify(result)

                if (str(form_otp).strip() == str(session.get('otp')).strip()):
                    usersDAO.update_user({"phone_is_valid": True, "user_id": session.get("id")})
                    session["phone_is_valid"] = True
                    result.update({'status': 204, "body": {'status': True, 'message': 'otp'}})
                else:
                    result.update({'status': 204, "body": {'status': False, 'message':"The key you entered is invalid."}})
                    return jsonify(result)
            else:
                url = config.API_SERVER['private_dashboard'] + "/api/user/verifyphone"
                r = requests.post(url, data={'phone': session.get("phone"), 'user_id': session.get("id",'')})
                phone_verify_data = r.json()
                session['otp'] = phone_verify_data['otp']
                result.update({'status': 204, "body": {
                        'status': True, 'message': 'phone'}})
                return redirect("/verifyphone")
        else:
            return redirect("/login")
    return jsonify(result)


def edit_phone():
    if session.get('phone_is_valid', ''):
        return redirect(decision())
    else:
        result = copy.deepcopy(session.get("header", {}))
        if session.get('id', ''):
            session['phone'] = None
            session['otp'] = None
            result.update({
                'status': 204,
                "body": {'status': True}
            })
            return redirect("/verifyphone")
        else:
            return redirect("/login")
    return jsonify(result)


def decision():
    return "/order_schedule"


def logout():
    session.clear()
    return redirect('/')
    # return redirect('http://%s' % app.config['DEFAULT_HOST_NAME'])


def verify_domain_auth():
    return open(os.path.dirname(app.config['BASE_DIR']) + "/13C8119BCAB31B5ADED9C94FAC94DE58.txt").read()