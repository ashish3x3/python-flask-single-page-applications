from flask.ext.restful import Resource
from flask import jsonify, request, session
import datetime
from mywash_admin import app
import copy
import bson
import random
import json
import requests

from mywash_admin import settings
from api.models import ServiceType as ServiceTypeModel
from mywash_admin.lib import emails

from oauth2client.client import verify_id_token
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
import httplib2
from mywash_admin.lib.loggers import MongoLogger


db = app.config['MONGO_CLIENT']['dealsup']

TIMESLOTS = app.config['TIMESLOTS']

LOGGER = MongoLogger('mywash_logs', 'missing_phone_logs')
EXCEPTION_LOGGER = MongoLogger('mywash_logs', 'exception_logs')


class ServiceType(Resource):
    def get(self):
        try:
            result = []
            services = ServiceTypeModel.query.all()
            for service in services:
                result.append({
                    'id': service.id,
                    'name': service.name
                })
            return result
        except Exception, e:
            print e
            return {'status': 'failure', 'error': 'db error.'}


class PickupSheetInfo(Resource):
    def base_info(self):
        return {
            'schedules': "",
            'address': "",
            'user': {
                'name': "",
                'phone': "",
                'email': "",
            },
        }

    def get(self, order_ids):
        try:
            order_ids = json.loads(order_ids)
            order_ids = [bson.ObjectId(order) for order in order_ids]
        except Exception:
            return jsonify({'status': "Invalid json format."}), 500

        user_ids = []
        schedule_ids = []
        address_ids = []
        orders = None
        try:
            orders = db.orders.aggregate([
                {'$project': {'user_id': 1, 'pickup_id': 1, 'delivery_id': 1, 'address_id': 1, 'phone': 1, 'order_id': 1}},
                {'$match': {'_id': {'$in': order_ids}}}
            ])
            for order in orders['result']:
                user_ids.append(order['user_id'])
                address_ids.append(bson.ObjectId(order['address_id']))
                schedule_ids.append(order['pickup_id'])
                schedule_ids.append(order['delivery_id'])
        except Exception:
            return jsonify({'status': "Db error."}), 500
        
        schedules_dict = {}
        try:
            schedules = list(db.schedules.find(
                {'_id': {'$in': schedule_ids}},
                {'address_id': 0, 'is_active': 0, 'user_id': 0, 'updated-date': 0, 'is_completed': 0, 'agent_id': 0, 'created_date': 0}
            ))
            for schedule in schedules:
                schedule['_id'] = str(schedule['_id'])
                schedules_dict[schedule['_id']] = schedule
        except Exception:
            return jsonify({'status': "Db error."}), 500

        users_dict = {}
        try:
            users = db.users.find({'user_id': {'$in': user_ids}})
            for user in users:
                users_dict[user['user_id']] = user
        except Exception:
            return jsonify({'status': "Db error."}), 500

        addresses_dict = {}
        try:
            addresses = db.addresses.find(
                {'_id': {'$in': address_ids}},
                {'is_active': 0, 'tag': 0, 'latitude': 0, 'longitude': 0, '_id': 0}
            )
            for address in addresses:
                addresses_dict[address['user_id']] = address
        except Exception:
            return jsonify({'status': "Db error."}), 500

        return_data = []
        for order in orders['result']:
            item = self.base_info()
            item['order_id'] = str(order['_id'])
            item['real_order_id'] = str(order['order_id']) if 'order_id' in order else ""
            item['address'] = addresses_dict[order['user_id']]
            item['schedules'] = {
                'pickup': schedules_dict[str(order['pickup_id'])],
                'delivery': schedules_dict[str(order['delivery_id'])],
            },
            item['user']['name'] = users_dict[order['user_id']]['name']
            item['user']['phone'] = order['phone'] if 'phone' in order else ""
            item['user']['email'] = users_dict[order['user_id']]['email'] if 'email' in users_dict[order['user_id']] else ''
            return_data.append(item)

        return jsonify({'data': return_data})


class UserLogin(Resource):
    access_token = None

    def get_user(self, user_id):
        try:
            orders = db.users.find({"user_id": user_id})
            json_docs = []
            for order in orders:
                result = copy.deepcopy(order)
                for k, v in order.items():
                    if isinstance(v, bson.ObjectId):
                        result[k] = str(v)
                    elif isinstance(v, datetime.date):
                        result[k] = v.strftime("%b %d %Y %H:%M")
                json_docs.append(result)
            return json_docs[0]
        except Exception as e:
            print "Failed to get user with exception ", str(e)
        return None

    def user_exists(self, user_id):
        try:
            orders = db.users.find_one({"user_id": user_id})
            if orders:
                return True
        except Exception as e:
            print "Failed to find if user exists with exception ",str(e)
        return False

    def base_user(self, user_id):
        if self.user_exists(user_id):
            print "user exists for id ",user_id
            return self.get_user(user_id)
        else:
            print "user doesn't exist for id ",user_id
            return {
                "user_id": "",
                "email": "",
                "name": "Raghu",
                "pictureUrl": "",
                "credits": 0,
                "phone": "",
                "createdAt": datetime.datetime.now(),
                "updatedAt": datetime.datetime.now(),
                "authData": {
                    "facebook": {
                        "id": "1067643280",
                        "access_token": "CAAEpRtuEZBOgBAAZBtHiMuf5qnOo4gKHG2vGMybJUZAujSpCgSLu8Ftqlss9Io9XJvuTHmznYZBVTNBopxZAYjUy0LfuRFtWy39IEyTQfDwFFmRAAY184aFQbdPjqYvgkSeUIvT6sWPQDmbnbXBULkHoWNVo4mUaHtf2hZBCZBpJHZCOyGXgAtKZBlJMCGPBMpjbpxTmCWtm3XtOaJh0NWPdTjCeynh9DZCXcZD",
                    }
                },
            }

    def get_fb_data(self, access_token):
        try:
            payload = {"access_token": access_token, "fields": "id,name,picture,email"}
            response = requests.get("https://graph.facebook.com/me", params=payload)

            response_json = response.json()
            session["me"] = response_json
            session["id"] = "fb_" + response_json.get("id")
            session['header'] = {'user': {"name": "", "pictureUrl": "", "id": ""}}
            base_user_data = self.base_user(session.get("id"))

            insert_data = {}
            try:
                session['header']['user']['pictureUrl'] = response_json.get("picture",{"data":""}).get("data").get("url")
                insert_data["pictureUrl"] = response_json.get("picture",{"data":""}).get("data").get("url")
            except Exception as e:
                session['header']['user']['pictureUrl'] = "//graph.facebook.com/"+str(response.json().get("id"))+"/picture?type = square"
                insert_data["pictureUrl"] = "//graph.facebook.com/"+str(response.json().get("id"))+"/picture?type = square"
                print "Failed to get pictureUrl from fb with exception : ", str(e)
            session['header']['user']['id'] = response_json.get("id")
            session['header']['user']["name"] = response_json.get("name", "")
            session["header"]["user"]["type"] = "fb"
            session["header"]["user"]["email"] = response_json.get("email", '')
            session["type"] = 2
            session["header"]["user"]["credits"] = base_user_data.get("credits", 0)
            session["header"]["user"]["phone"] = base_user_data.get("phone", 0)
            
            insert_data["user_id"] = session.get("id")
            insert_data["name"] = response_json.get("name", "")
            insert_data["email"] = response_json.get("email", '')
            insert_data["authData"] = copy.deepcopy(session.get("header")["user"])
            insert_data["authData"]["access_token"] = access_token
            insert_data['headers'] = {'user_agent': request.headers.get('User-Agent', '')}
            
            if self.user_exists(insert_data.get("user_id")):
                insert_data["updatedAt"] = datetime.datetime.now()
                device_id = set(db.users.find_one({'user_id': insert_data.get("user_id")}).get('device_id', []))
                device_id.add(self.device_id)
                insert_data['device_id'] = list(device_id)
                result = db.users.update(
                    {'user_id': insert_data.get("user_id")},
                    {'$set': insert_data}
                )
            else:
                datetime_now = datetime.datetime.now()
                insert_data["createdAt"] = datetime_now
                insert_data["updatedAt"] = datetime_now
                insert_data['device_id'] = [self.device_id]
                db.users.insert(insert_data)
                emails.email_welcome({
                    "email": insert_data["email"],
                    "name": insert_data["name"]
                })
        except Exception as e:
            EXCEPTION_LOGGER.error(
                "fb common error",
                event='get_android_data.fb_common_error'
            )
            print "Failed to set me data in session with exception : ", str(e)
            return jsonify({'status': 'failure', "error": 'db error'}), 403
        return jsonify({'status': 'success', 'id': insert_data.get("user_id")})

    def get_android_data(self, id_token, code=None):
        try:
            jwt = verify_id_token(id_token, settings.GPLUS_CREDS['client_id'])
        except Exception as e:
            EXCEPTION_LOGGER.error(
                "jwt retrive error",
                event='get_android_data.jwt_retrive_error'
            )
            return {'status':'failure', 'error':'AppIdentityError: Invalid id_token'}
        insert_data = {}
        # If multiple clients access the backend server:
        if jwt['aud'] != settings.GPLUS_CREDS['client_id'] or jwt['azp'] != settings.GPLUS_CREDS['android_client_id']:
            return {'status': 'failure', 'error': "AppIdentityError: Unrecognized client."}

        if jwt['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return {'status': 'failure', 'error': "AppIdentityError: Wrong issuer."}
        if jwt['sub'] is None:
            return {'status': 'failure', 'error': "User ID not found."}
        else:
            try:
                insert_data = {'user_id': 'g_'+jwt['sub']}
                if self.user_exists(insert_data.get("user_id")):
                    try:
                        payload = {'fields': 'displayName,image,id', 'key':settings.GPLUS_CREDS['api_key']}
                        json_data = requests.get('https://www.googleapis.com/plus/v1/people/'+jwt['sub'], params=payload).json()
                    except Exception as e:
                        print e
                        return {'status':'failure', 'error':'Googleapis error.'}, 403
                    if 'image' in json_data:
                        insert_data['pictureUrl'] = json_data['image']['url']
                    if 'name' in json_data:
                        insert_data['name'] = json_data['displayName']
                    insert_data['android_credentials'] = id_token
                    try:
                        insert_data["updatedAt"] = datetime.datetime.now()
                        device_id = set(db.users.find_one({'user_id': insert_data.get("user_id")}).get('device_id', []))
                        if device_id:
                            device_id.add(self.device_id)
                        insert_data['device_id'] = list(device_id)
                        insert_data['headers'] = {'user_agent': request.headers.get('User-Agent', '')}
                        result = db.users.update(
                            {'user_id': insert_data.get("user_id")},
                            {'$set': insert_data}
                        )
                    except Exception as e:
                        EXCEPTION_LOGGER.error(
                            "update user data",
                            event='get_android_data.update_user_data'
                        )
                        return {'status':'failure', 'error':'User data Updation error.'}, 403
                else:
                    try:
                        flow = OAuth2WebServerFlow(client_id=settings.GPLUS_CREDS['client_id'],
                                client_secret=settings.GPLUS_CREDS['client_secret'],
                                scope=settings.GPLUS_CREDS['scopes'],
                                redirect_uri=settings.GPLUS_CREDS['redirect_uri']
                        )
                    except Exception as e:
                        EXCEPTION_LOGGER.error(
                            "oauth flow error",
                            event='get_android_data.oauth_flow_error'
                        )
                        return {'status': 'failure', 'error':'creds'}
                    
                    try:
                        credentials = flow.step2_exchange(code)
                        user_info_service = build(
                            serviceName='oauth2', version='v2',
                            http=credentials.authorize(httplib2.Http())
                        )
                        user_info = user_info_service.userinfo().get().execute()
                    except Exception as e:
                        EXCEPTION_LOGGER.error(
                            "step 2 exchange",
                            event='get_android_data.step_2_exchange'
                        )
                        return {'status': 'failure', 'error': 'Data not found'}
                    
                    try:
                        print 'User Info', user_info
                        insert_data['device_id'] = [self.device_id]
                        insert_data['pictureUrl'] = user_info['picture']
                        insert_data['name'] = user_info['name']
                        insert_data['user_id'] = 'g_'+user_info['id']
                        insert_data['android_credentials'] = id_token
                        insert_data['authData'] = {
                            'id': user_info['id'],
                            'type': 'google'
                        }
                        insert_data['headers'] = {'user_agent': request.headers.get('User-Agent', '')}
                        datetime_now = datetime.datetime.now()
                        insert_data["createdAt"] = datetime_now
                        insert_data["updatedAt"] = datetime_now
                        print insert_data
                        db.users.insert(insert_data)
                    except Exception as e:
                        EXCEPTION_LOGGER.error(
                            "user creation error",
                            event='get_android_data.user_creation_error'
                        )
                        return {'status': 'failure', 'error': 'New data insertion error'} 
            except Exception as e:
                EXCEPTION_LOGGER.error(
                    "common error",
                    event='get_android_data.common_error'
                )
                return {'status': 'failure', 'error': "Request error"}

        return {'status': 'success', 'id': insert_data['user_id']}

    def get_google_data(self, access_token):
        try:
            payload = {"access_token": access_token}
            response = requests.get("https://www.googleapis.com/plus/v1/people/me", params=payload)
            response_data = response.json()
            session["me"] = response_data
            session["id"] = "g_"+response_data.get("id")
            session['header'] = {'user': {"name": "", "pictureUrl": "", "id": ""}}
            # The below line has to be changed to put the db id
            base_user_data = self.base_user(session.get("id"))
            
            session['header']['user']['pictureUrl'] = response_data.get("image", {"url": ""}).get("url")
            session['header']['user']['id'] = response_data.get("id")
            session['header']['user']["name"] = response_data.get("name","").get("givenName", "")+" "+response_data.get("name", "").get("familyName", "")
            session["header"]["user"]["type"] = "google"
            session["header"]["user"]["email"] = response_data.get("emails")[0].get("value", "")
            session["type"] = 1
            session["header"]["user"]["credits"] = base_user_data.get("credits", 0)
            session["header"]["user"]["phone"] = base_user_data.get("phone", 0)

            insert_data = {}
            insert_data["pictureUrl"] = response_data.get("image", {"url": ""}).get("url")
            insert_data["user_id"] = session.get("id")
            insert_data["name"] = response_data.get("name", "").get("givenName", "")+" "+response_data.get("name", "").get("familyName", "")
            
            try:
                insert_data["email"] = response_data.get("emails")[0].get("value","")
            except Exception,e:
                pass
            insert_data["authData"] = copy.deepcopy(session.get("header")["user"])
            insert_data["authData"]["access_token"] = session.get("access_token")
            insert_data['headers'] = {'user_agent': request.headers.get('User-Agent', '')}

            if self.user_exists(insert_data.get("user_id")):
                insert_data["updatedAt"] = datetime.datetime.now()
                device_id = set(db.users.find_one({'user_id': insert_data.get("user_id")}).get('device_id', []))
                if device_id:
                    device_id.add(self.device_id)
                insert_data['device_id'] = list(device_id)
                result = db.users.update(
                    {'user_id': insert_data.get("user_id")},
                    {'$set': insert_data}
                )
            else:
                datetime_now = datetime.datetime.now()
                insert_data["createdAt"] = datetime_now
                insert_data["updatedAt"] = datetime_now
                insert_data['device_id'] = [self.device_id]
                db.users.insert(insert_data)
                emails.email_welcome({
                    "email": insert_data["email"],
                    "name": insert_data["name"]
                })
        except Exception as e:
            print "Failed to set me data in session with exception : ", str(e)
            return jsonify({'status': 'failure', "error": 'db error'}), 403
        return jsonify({'status': 'success', 'id': insert_data.get("user_id")})
    
    def post(self):
        form = copy.deepcopy(request.form)
        if 'type' not in form:
            return {'status': 'failure', 'error': 'Login type not provided.'}, 403
        
        if 'device_id' not in form:
            return {'status': 'failure', 'error': 'Device id not provided.'}, 403
        else:
            self.device_id = form['device_id'].strip()
        
        if form['type'] == 'fb':
            if 'access_token' not in form:
                return {'status': 'failure', 'error': 'Access token not provided.'}, 403
            return self.get_fb_data(form['access_token'])
        elif form['type'] == 'google':
            if 'access_token' not in form:
                return {'status': 'failure', 'error': 'Access token not provided.'}, 403
            return self.get_google_data(form['access_token'])
        elif form['type'] == 'android':
            if 'id_token' not in form:
                return {'status': 'failure', 'error': 'ID token not provided.'}, 403
            if 'auth_code' in form:
                return self.get_android_data(form['id_token'], form['auth_code'])
            else:
                return self.get_android_data(form['id_token'])
        return {'status': 'failure', 'error': 'Login type not listed.'}, 403


class AndroidScopes(Resource):
    def get(self):
        return {'scopes': app.config['GPLUS_CREDS']['scope']}


class AndroidConfig(Resource):
    def get(self, **kwargs):
        redis_client = app.config['REDIS_CLIENT']
        if 'agent' in kwargs:
            return {
                'version': redis_client.hget('ANDROID_AGENT_UPDATE', 'version'),
                'recommended': redis_client.hget('ANDROID_AGENT_UPDATE', 'recommended'),
                'mandatory': redis_client.hget('ANDROID_AGENT_UPDATE', 'mandatory'),
            }
        else:
            return {
                'version': redis_client.hget('ANDROID_UPDATE', 'version'),
                'recommended': redis_client.hget('ANDROID_UPDATE', 'recommended'),
                'mandatory': redis_client.hget('ANDROID_UPDATE', 'mandatory'),
                'min_supported_version': redis_client.hget('ANDROID_UPDATE', 'min_supported_version')
            }


class SendSMS(Resource):
    def post(self):
        form = copy.deepcopy(request.form)
        if 'phone' not in form:
            return {'status': 'failure', 'error': 'Phone number not provided.'}, 403

        if 'sms' not in form:
            return {'status': 'failure', 'error': 'Sms body not provided.'}, 403

        emails.mywash_order_transactional_sms(form['phone'], form['sms'])
        return {'status': 'success'}


class PhoneVerification(Resource):
    def post(self):
        form = copy.deepcopy(request.form)
        if 'user_id' not in form and not form['user_id']:
            return {'status': 'failure', 'error': 'User id not provided.'}, 403

        if 'phone' not in form and form['phone']:
            return {'status': 'failure', 'error': 'Phone number not provided.'}, 403

        insert_data = {}
        insert_data["phone"] = form['phone']

        if not insert_data['phone'].strip():
            global LOGGER
            LOGGER.error(
                "missing phone number",
                event='missing_phone_event',
                user_id=form['user_id'],
                user_agent=request.headers.get('User-Agent', '')
            )

        if not (len(insert_data.get('phone')) == 10 and insert_data.get('phone').isdigit()):
            return {'status': 'failure', 'error': 'Invalid Phone Number Format. Please enter a valid 10 digit phone number '}, 403
        
        try:
            user = db.users.find_one({"user_id": insert_data.get('user_id')})
        except Exception, e:
            print e
            return {'status': 'failure', 'error': "db error"}, 500
        user_data =''

        if user:
            try:
                user_data = db.users.find_one({"phone": insert_data.get("phone"), "phone_is_valid":True})
            except Exception, e:
                print e
                return {'status': 'failure', 'error': "db error"}, 500

            insert_data["phone_is_valid"] = True

            if user_data:
                if user_data['user_id'] == form['user_id']:
                    return {'status': 'success', 'message': 'User validated by phone'}
                else:
                    return {'status': 'failure', 'error': ["As per new MyWash policy, a user cannot have multiple accounts with the same mobile number.","Your number "+insert_data.get('phone')+" is already registered with another account. You may logout, and login again from the other account.","Alternatively, you may register a new number with this account."]},403
            else:
                try:
                    result = db.users.update(
                        {'user_id': form['user_id']},
                        {'$set': insert_data}
                    )
                except Exception, e:
                    print e
                    return {'status': 'failure', 'error': "db error"}, 500
        else:
            return {'status': 'failure', 'error': 'Oops, something went wrong. Invalid User.'}, 403    

        return {'status': 'success', 'message': 'User phone verified successfully'}


class PhonePushNotification(Resource):
    def __send_parse_notification(self, alert):
        try:
            result = requests.post("https://api.parse.com/1/push", data=json.dumps({
                "where": {
                    "installationId": "aec625be-7342-4dbf-bde7-b4f01236797c",
                },
                "data": {
                    "alert": alert,
                    "title": "test notification!"
                }
            }), headers={
                "X-Parse-Application-Id": "yXqFau0gdsr7uh1H0yiSFeoXCtk16Ht3UMSpgCfx",
                "X-Parse-REST-API-Key": "lxLkg0SNfIlFGiV3plIGDmV6GvS3u4SY22AMLQTy",
                "Content-Type": "application/json"
            })
            
            return json.loads(result.json())
        except Exception, e:
            print e
            return {'status': 'failure', 'error': ' parse failure '}, 500

    def post(self):
        form = copy.deepcopy(request.form)
        if 'alert_message' not in form and not form['alert_message']:
            return {'status': 'failure', 'error': 'No alert message'}, 403

        result = self.__send_parse_notification(form['alert_message'])

        return result


