#!/usr/bin/env python
#original
import os
import sys
#sys.path.insert(0, '/home/prashanth/mywash_code/boiler/boiler')
# Flask
from flask import Flask, render_template
from boiler.service.redis import redis_session
from flask_debugtoolbar import DebugToolbarExtension
from boiler import config

app = Flask(__name__)

### ALL THE SETTINGS ARE DONE HERE ###
#getting the redis credentials from config.py file for app.session_interface
app.session_interface = redis_session.RedisSessionInterface(
    conf=config.REDIS_CREDS, prefix="main_session:")

# Load app config ->config.py file  Then all the configuration values will be loaded into the app.config dictionary
#reference: http://stackoverflow.com/questions/15122312/how-to-import-from-config-file-in-flask
app.config.from_object(config)
# stores all the settings from config.py to settings
settings = app.config

# Load all packages to sys.path for import support
for root, dirs, files in os.walk(settings['BASE_DIR']):
    if os.path.isfile(os.path.join(root, '__init__.py')):
        if root not in sys.path:
            sys.path.append(root)

# Config
if app.config['DEBUG']:
    app.debug = True
    #creating a new key ASSETS_DEBUG into config if DEBUG exists
    app.config['ASSETS_DEBUG'] = True

### END OF SETTINGS ###

#referecne: https://www.youtube.com/watch?v=jELLsj1KPNQ
#above video helps understand the code in frontend.py and errorhandler code below
from controllers import frontend
import filters

from boiler.models.database import db

#here db.statuses.find() is a mongo function that returns the data from statuses table
statuses = list(db.statuses.find())

def getStatusDetail(name_id):
    for status_group in statuses:
        for status in status_group['status']:
            if name_id == status['name_id']:
                status['group_id'] = status_group['group_id']
                status['group_name'] = status_group['group_name']
                return status
app.config['GET_STATUS_DETAIL'] = getStatusDetail
app.secret_key = "hghjgjgj"


#the logging code below is for viewing on the webside
import logging
logging.basicConfig(
    level=logging.DEBUG,

    format='[%(asctime)s] [%(filename)s] [%(funcName)s] [%(levelname)s] %(message)s',
    datefmt='%Y%m%d-%H:%M%p',
)

from functools import wraps
def custom_error(f):
    @wraps(f)
    def err_f(msg, *args, **kwargs):
        kwargs['exc_info']=True
        return f(msg, *args, **kwargs)

@app.errorhandler(404)
def internal_error(e):
    return render_template('errors/404.jinja'), 404


@app.errorhandler(500)
def internal_error(e):
    return render_template('errors/500.jinja'), 500

