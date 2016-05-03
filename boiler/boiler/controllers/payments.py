import copy
import requests
import sys
import json
import traceback

from flask import jsonify, request, redirect

from boiler.models.database import logger as mongo_logger
from boiler import config

"""
On redirection from payment page Paytm sends the following parameters to /payment/success
>> ORDERID
>> STATUS  can be TXN_SUCCESS/TXN_FAILURE/TXN_PENDING
>> GATEWAYNAME can be ICICI/CITI/WALLET
>> RESPCODE
>> TXNDATE '2015-08-20 17:14:48.0'
>> TXNID
>> BANKTXNID
>> BANKNAME
>> PAYMENTMODE
>> MID
>> CURRENCY
>> RESPMSG
>> TXNAMOUNT
>> CHECKSUMHASH
"""


def payment():
    try:
        payment_res = copy.deepcopy(request.form)
        result = requests.put(config.API_SERVER['private_dashboard'] + "/api/paytm/payment", data=payment_res).json()
        if result['status'] == 'success':
            if payment_res['RESPCODE'] == '01':
                return redirect(config.WEBSITE + '/getstatus/' + result['order_id'] + "?transaction_status=failure&transaction_message=" + payment_res['RESPMSG'])
            else:
                return redirect(config.WEBSITE + '/getstatus/' + result['order_id'])
        else:
            return redirect(config.WEBSITE + '/orders')
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log = {
            'event': 'Payment Exception',
            'exception': repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            'form_data': json.dumps(copy.deepcopy(request.form))
        }
        mongo_logger.exception_logs.insert(log)
        return jsonify({'status': 'failure', 'error': str(e)}), 403


def checksum_validation():
    try:
        payment_res = copy.deepcopy(request.form)
        result = requests.put(config.API_SERVER['private_dashboard'] + "/api/paytm/payment", data=payment_res).json()
        if result['status'] == 'success':
            if payment_res['RESPCODE'] == '01':
                return redirect(config.WEBSITE + '/getstatus/' + result['order_id'] + "?transaction_status=failure&transaction_message=" + payment_res['RESPMSG'])
            else:
                return redirect(config.WEBSITE + '/getstatus/' + result['order_id'])
        else:
            return redirect(config.WEBSITE + '/orders')
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 403


def checksum_generation():
    try:
        payment_res = copy.deepcopy(request.form)
        result = requests.put(
            config.API_SERVER['private_dashboard'] + "/api/paytm/checksum/genaration",
            data=payment_res
        ).json()
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 403
