from boiler.models.dao import usersDAO, addressDAO, schedulesDAO
from flask import jsonify,request,session,render_template,redirect
import Constants
import datetime,copy,logging
from boiler.renderer import commonrender
import requests
from boiler import app


def submit_address():
    try:
        result=copy.deepcopy(session.get("header",{}))
        if request.method=='POST':
            data=addressDAO.base_address()
            print request.form

            copy_data=copy.deepcopy(request.form)

            data["latitude"]=copy_data.get("latitude")
            data["longitude"]=copy_data.get("longitude")

            address_list = addressDAO.get_user_address(session.get("id","")).get("result")

            try:

                tag = copy_data.get("tag") if copy_data.get("tag")!="" else copy_data.get("address_1")[:4]
                data['tag'] = tag

            except Exception,e:
                print str(e)
                data['tag'] = "Default"

            data["is_active"]=True
            data["pincode"]=copy_data.get("pincode")

            data["address_1"]=copy_data.get("address_1")
            data["address_2"]=copy_data.get("address_2")
            data["apartment_number"]=copy_data.get("apartment_number")
            data["user_id"]=session.get("id")

            print data

            address_id=addressDAO.add_address(data)

    except Exception,e:
        print str(e)
        address_id=0

    if address_id >0:
        result.update({"status": 204, "body": {"status": True, "address":{"id":address_id}}})
    else:
        result.update({"status": 204, "body": {"status": False, "message": "Failed to address"}})
    return jsonify(result)


def submit_address_cors():
    form = copy.deepcopy(request.form)
    address_index = form['address_index'] if 'address_index' in form else None
    payload = {
        'tag': form['tag'],
        'apartment_number': form['apartment_number'],
        'address_1': form['address_1'],
        'address_2': form['address_2'],
        'locality': form['locality'],
        'user_id': form['user_id'],
    }
    result = None
    if address_index is None:
        result = requests.post(app.config['API_SERVER']['private_dashboard'] + "/api/address", data=payload)
    else:
        result = requests.put(
            app.config['API_SERVER']['private_dashboard'] + "/api/address/%s" % form['address_index'],
            data=payload
        )
    if result.status_code == 200:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure'}), 403


def update_locality():
    form = copy.deepcopy(request.form)
    payload = {
        'locality': form['locality']
    }
    result = requests.put(
        app.config['API_SERVER']['private_dashboard'] + "/api/address/%s" % form['address_id'],
        data=payload
    )
    if result.status_code == 200:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure'}), 403


def get_address():
    try:
        user_id=session.get("id")
        result=copy.deepcopy(session.get("header",{}))
        result.update(addressDAO.get_user_address(user_id))
    except Exception,e:
        result=[]
    return jsonify(result)


def edit_address():
    result = copy.deepcopy(session.get("header",{}))
    copy_data = copy.deepcopy(request.form)


    if request.method == 'POST':

        if copy_data.get('form_action') == 'save':
            try:
                updated_address = addressDAO.update_address({
                                        "tag": copy_data.get("tag"),
                                        "apartment_number": copy_data.get("apartment_number"),
                                        "address_1": copy_data.get("address_1"),
                                        "address_2": copy_data.get("address_2"),
                                        "user_id": session.get("id",""),
                                    }, copy_data.get('object_id',''))
                print updated_address
                if updated_address:
                    result.update(addressDAO.get_user_address(session.get('id','')))
                return redirect('/myprofile')
            except Exception as e:
                print e

        elif copy_data.get('form_action') == 'delete':

            try:
                if addressDAO.remove_address(copy_data.get('object_id','')):
                    print "address removed"
                else:
                    print "failed to remove"
                return redirect('/myprofile')
            except Exception as e:
                print e


@commonrender("profile/add_address.html")
def show_address_edit_page(address_id=None):
    result = copy.deepcopy(session.get("header",{}))
    result['user_id'] = session.get('id','')
    if session.get('id',''):
        if address_id is not None:
            address = addressDAO.get_address(address_id)['result'][0]
            if address['user_id'] != session.get('id',''):
                return {'status': 'failure'}, 500
            result.update({"address": address})
            result['add_address'] = False
        else:
            result.update({"address": None})
            result['add_address'] = True
        return result
    else:
        return redirect('/order_schedule')
