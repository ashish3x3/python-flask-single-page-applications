from flask import Flask
# from flask.ext.mongoengine import MongoEngine
from flask import Flask
from flask.ext import restful
import settings
import os
import importlib

app = Flask(__name__)

for path in os.listdir(settings.BASE_DIR):
    if os.path.isdir(os.path.join(settings.BASE_DIR, path)):
        if os.path.isfile(os.path.join(settings.BASE_DIR, path, "models.py")):
            try:
                module = importlib.import_module("%s.models" % path)
            except Exception, e:
                print e
                raise Exception()


api = restful.Api(app)
