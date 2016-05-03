from boiler.models.database import logger as mongo_logger
from boiler.models.dao import ordersDAO
from boiler.models.dao import schedulesDAO
from boiler.models.dao import addressDAO
from boiler.models.dao import itemsDAO
from boiler.models.dao import usersDAO
from flask import jsonify, request, session
from flask import render_template, redirect, make_response
import Constants
import copy, json, logging, requests
from boiler.renderer import commonrender
import emails, sms
from boiler import app
from boiler import config
from datetime import datetime
from urllib2 import URLError
import traceback
import sys
from requests_futures.sessions import FuturesSession


@commonrender('enterprise/login.jinja')
def enterprise_login():
    result = copy.deepcopy(session.get("header", {}))
    copy_data = copy.deepcopy(request.form)
    return result


def validate_enterprise_login():
    print "In validation"
    result = copy.deepcopy(session.get("header", {}))
    copy_data = copy.deepcopy(request.form)
    payload = {}
    for data in copy_data:
        payload[data] = copy_data[data]
    print payload
    data = requests.get('http://localhost:5000/api/partner/login', params=payload)
    print data.json()
    return data.json()