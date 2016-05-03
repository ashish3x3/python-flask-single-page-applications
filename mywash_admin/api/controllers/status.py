from flask.ext.restful import Resource
from flask import jsonify, request
from mywash_admin import app
import pymongo


db = app.config['MONGO_CLIENT']['dealsup']


class StatusList(Resource):
    def get(self):
        return jsonify({"data": list(db.statuses.find())})