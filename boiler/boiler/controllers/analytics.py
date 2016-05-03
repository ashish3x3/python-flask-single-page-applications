from boiler.models.dao import analyticsDAO
from flask import jsonify,request,session,render_template

def submit_post():
    return True


def add_post_view(count):
    result_set=postsDAO.get_top(count)
    return jsonify(result_set)


def get_post(post_id):
    result=postsDAO.get_post(post_id)
    return True


def trending():
    count = request.args.get("count",5)
    result=postsDAO.get_trending(count)
    return result
