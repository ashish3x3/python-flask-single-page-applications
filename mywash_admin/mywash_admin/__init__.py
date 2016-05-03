from flask import Flask, request, session
from flask.ext import restful
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.migrate import Migrate
import settings
import os
import importlib
from mywash_admin.lib.url_converters import RegexConverter
from mywash_admin.lib.redis_session import RedisSessionInterface
from celery import Celery
from flask_cors import CORS
from mywash_admin.lib.loggers import MongoLogger
# from raven.contrib.flask import Sentry


app = Flask(__name__)
app.session_interface = RedisSessionInterface(conf=settings.REDIS_CREDS)
app.config.from_object(settings)
app.url_map.converters['regex'] = RegexConverter

db = SQLAlchemy(app)
# sentry = Sentry(app)

migrate = Migrate(app, db)

for path in os.listdir(settings.BASE_DIR):
    if os.path.isdir(os.path.join(settings.BASE_DIR, path)):
        if os.path.isfile(os.path.join(settings.BASE_DIR, path, "models.py")):
            try:
                module = importlib.import_module("%s.models" % path)
            except Exception, e:
                print e
                raise Exception()


api = restful.Api(app)

from mywash_admin.lib import filters

cors = CORS(app)

REQUEST_LOGGER = MongoLogger('mywash_logs', 'request_logs')
@app.before_request
def before_request(*args, **kwargs):
    if session.get('emp_data', False):
        REQUEST_LOGGER.info(
            'request logging',
            event='request_logging',
            url=request.url,
            form=request.form,
            email=session['emp_data']['email']
        )

# @app.after_request
# def after_request(response):
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
#     return response


# Initialize Celery
celery = Celery(app.config['APP_NAME'])
celery.config_from_object(app.config['CELERY_CONFIG']())
