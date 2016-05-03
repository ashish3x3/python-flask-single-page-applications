import requests
import json
from boiler import config
from flask import session, jsonify, request,make_response
from boiler.celery_app.celeryconfig import celery
import sys

import geoip2.database
from boiler.models.dao import usersDAO


@celery.task
def set_activity(activityName):
	
	mail = None

	user_token_mywash = request.cookies.get('_utmw')
	if user_token_mywash:#having token and no session
		user = usersDAO.get_emailByObjId(user_token_mywash)
		mail = user['email']
		if mail:
			#http://stackoverflow.com/questions/3759981/get-ip-address-of-visitors-using-python-flask
			userip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
			userAgentString = str(request.user_agent)
			cookies = request.cookies
			userproperties = session.get("header",{})
			print "file ->>",__file__
			#geoip2.database.Reader('./geoip2/GeoLite2-City.mmdb')
			reader = config.GEOIPDB
			geoipdetails =""
			if userip!="127.0.0.1":
				geoipdetails = reader.city(userip)
			else:
				geoipdetails = reader.city("103.227.97.237")

			jdata = {}
			jdata["iso_code"] = str(geoipdetails.country.iso_code)
			jdata["region"] = str(geoipdetails.subdivisions.most_specific.name)
			jdata["postalcode"] = geoipdetails.postal.code
			jdata['latitude'] = str(geoipdetails.location.latitude)
			jdata['longitude'] = str(geoipdetails.location.longitude)
			jdata['country'] = str(geoipdetails.country.name)
			jdata['city'] = str(geoipdetails.city.name)


			dumps = {"activity": {"user": {'email':mail},"properties":{'id':session.get("id"),'geoipdetails':json.dumps(jdata),'userip':userip,'user':userproperties,'cookies':cookies,'useragent':userAgentString},"event": activityName}}

			activity = json.dumps(dumps)
			nudge_cred = config.NUDGESPOT_CREDS
			r= requests.post(nudge_cred['URL_ACTIVITY'], data=activity, auth=(nudge_cred['USERNAME'], nudge_cred['API_KEY']), headers=config.NUDGESPOT_HEADER)
			print "nudgespot --> ",r
		else:
			print "nudgespot ---> cant access email"

