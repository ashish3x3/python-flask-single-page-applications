from flask import request,session,jsonify
from boiler.models.dao import itemsDAO
from boiler.renderer import commonrender
import copy

def get_item(item_id):
	result=copy.deepcopy(session.get("header",{}))
	result.update(itemsDAO.get_item(item_id))
	return jsonify(result)

@commonrender('pricing/pricing.jinja')
def get_all():
	result=copy.deepcopy(session.get("header",{}))
	result.update(itemsDAO.get_all_items())
	return result