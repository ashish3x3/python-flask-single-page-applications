import copy
import traceback
import sys
import requests
import urllib

from datetime import datetime
from bson.objectid import ObjectId

from flask.ext.restful import Resource
from flask import request

from mywash_admin.lib import emails
from mywash_admin import settings, app, db as pgdb
from api.controllers.checksum import generate_checksum, validate
from api.models import OnlineTransaction
from mywash_admin.lib.loggers import MongoLogger

EXCEPTION_LOGGER = MongoLogger('mywash_logs', 'exception_logs')

db = app.config['MONGO_CLIENT']['dealsup']


class PaytmPayment(Resource):
    def _check_txn_status(self, payment_id):
        try:
            url = settings.PAYTM_TXNSTATUS + \
                '?JsonData={"MID":"%s","ORDERID":"%s"}' % (settings.PAYTM_CRED['mid'], payment_id)
            txn_res = requests.post(url)
            return txn_res.json()
        except Exception as e:
            return {'status': 'failure', 'error': str(e)}

    def get(self, order_id):
        if not order_id:
            return {'status': 'failure', 'error': 'order_id not provided'}, 403

        try:
            order = db.orders.find_one({"_id": ObjectId(order_id)})
            user = db.users.find_one({"user_id": order['user_id']})
            payment_data = {}
            payment_data['REQUEST_TYPE'] = 'DEFAULT'
            payment_data['MID'] = settings.PAYTM_CRED['mid']
            if order.get('payment_id', False):
                txn_res = self._check_txn_status(order['payment_id'])
                if 'status' in txn_res and txn_res['status'] == 'failure':
                    return txn_res
                if txn_res['RESPCODE'] != '01':
                    txn = OnlineTransaction.query.filter(
                        OnlineTransaction.str_id == order['payment_id']
                    ).first()
                    txn.is_active = False
                    pgdb.session.add(txn)
                    pgdb.session.commit()
                else:
                    return {'status': "success", 'message': "Amount already paid"}

            try:
                txn = OnlineTransaction()
                payment_data['ORDER_ID'] = txn.str_id
                pgdb.session.add(txn)
                pgdb.session.commit()
                db.orders.update(
                    {"_id": ObjectId(order_id)},
                    {'$set': {'payment_id': payment_data['ORDER_ID']}}
                )
            except Exception as e:
                return {'error': "db error", 'status': "error"}, 500
            payment_data['CUST_ID'] = str(user['_id'])
            if 'is_paid' in order and order['is_paid'] == 'partially_paid':
                payment_data['TXN_AMOUNT'] = str(
                    float(order['total_price']) - float(order['cash_collected'])
                )
            else:
                payment_data['TXN_AMOUNT'] = str(float(order['total_price']))
            payment_data['INDUSTRY_TYPE_ID'] = settings.PAYTM_CRED['industry_type_id']
            payment_data['WEBSITE'] = settings.PAYTM_CRED['web']
            payment_data['CHANNEL_ID'] = 'WEB'
            # payment_data['MOBILE_NO'] = order.get('phone')

            # if 'email' in user and user['email']:
            #     payment_data['EMAIL'] = user.get('email')
            # elif 'email' in user['authData'] and user['authData']['email']:
            #     payment_data['EMAIL'] = user['authData']['email']

            # For Net Banking
            # payment_data['PAYMENT_MODE_ONLY'] = 'YES'
            # payment_data['AUTH_MODE'] = 'USRPWD'
            # payment_data['PAYMENT_TYPE_ID'] = 'NB'
            # payment_data['BANK_CODE'] = 'HDFC'

            payment_data['CHECKSUMHASH'] = generate_checksum(payment_data, settings.PAYTM_CRED['merchant_key'])
            url = settings.PAYTM_TRX_URL + payment_data['ORDER_ID']

            # if request.headers.get('User-Agent', '') == "android":
            #     payment_data['WEBSITE'] = settings.PAYTM_CRED['WAP']
            #     payment_data['CHANNEL_ID'] = 'WAP'
            #     payment_data.pop('CHECKSUMHASH')

            return {'payment_data': payment_data, 'url': url}
        except Exception, e:
            return {"status": "failure", "error": "Payment Failed: " + str(e)}, 403

    def put(self):
        payment_data = dict(copy.deepcopy(request.form))
        try:
            data = {}
            for key, value in payment_data.items():
                if value[0] != '':
                    payment_data[key] = value[0]
            order_txn_id = payment_data.pop('ORDERID')
            try:
                payment_data.pop('MID')
                payment_data.pop('CHECKSUMHASH')
                txn = OnlineTransaction.query.filter(OnlineTransaction.str_id == order_txn_id).first()
                order = db.orders.find_one({'payment_id': order_txn_id})
                if payment_data['RESPCODE'] == '01':
                    if 'CURRENCY' in payment_data:
                        payment_data.pop('CURRENCY')
                    if 'TXNDATE' in payment_data:
                        txn_date = payment_data.pop('TXNDATE')
                        txn.txn_date = datetime.strptime(
                            txn_date[:txn_date.index('.')],
                            '%Y-%m-%d %H:%M:%S')
                    if 'PAYMENTMODE' in payment_data:
                        payment_data['TYPE'] = "WALLET" if payment_data['PAYMENTMODE'] == 'PPI' else payment_data['PAYMENTMODE']
                    txn.is_active = True
                    data['is_paid'] = 'paid'
                    data['cash_collected'] = int(float(payment_data['TXNAMOUNT']))
                    sms = "Your payment of Rs." + \
                        str(payment_data['TXNAMOUNT']) + " for order ID #" + order['order_id'] + " was successful. Thank you for the order."
                else:
                    txn.txn_date = datetime.now()
                    if 'is_paid' not in order or order['is_paid'] != 'partially_paid':
                        data['is_paid'] = "not_paid"
                    sms = "Payment of order amount Rs." + \
                        str(payment_data['TXNAMOUNT']) + " for order ID #" + order['order_id'] + \
                        " was unsuccessful/pending. Thank you for the order."
                payment_data['SERVICE'] = 'PAYTM'
                data['payment_id'] = order_txn_id
                txn.data = payment_data
                txn.txn_type = 'online'
            except Exception as e:
                EXCEPTION_LOGGER.error({
                    'event': 'payment_put',
                    'args': payment_data
                })
                return {'status': 'failure', 'error': str(e)}, 500

            try:
                pgdb.session.add(txn)
                pgdb.session.commit()
                result = db.orders.update(
                    {'payment_id': order_txn_id},
                    {'$set': data}
                )

                emails.mywash_order_transactional_sms(
                    order['phone'].strip(),
                    sms,
                    order.get('partner_id', None)
                )
                print result
                return {'status': 'success', 'order_id': str(order['_id'])}, 200
            except Exception, e:
                EXCEPTION_LOGGER.error({
                    'event': 'payment_put',
                    'args': payment_data
                })
                return {'status': 'failure', 'error': 'db error.'}, 500
        except Exception, e:
            EXCEPTION_LOGGER.error({
                'event': 'payment_put',
                'args': payment_data
            })
            return {"status": "failure", "error": "Payment Failed: " + str(e)}, 403


class PaytmRefund(Resource):
    def _check_refund_status(self, payment_id, rfid):
        try:
            url = settings.PAYTM_REFUND_STATUS + \
                '?JsonData={"MID":"%s","ORDERID":"%s","REFID":"%s"}' % \
                (settings.PAYTM_CRED['mid'], payment_id, rfid)
            refund_res = requests.post(url)
            return refund_res.json()
        except Exception as e:
            return {'status': 'failure', 'error': str(e)}

    def get(self, order_id):
        try:
            order = db.orders.find_one({'_id': ObjectId(order_id)})
            txn = OnlineTransaction.query.filter(
                OnlineTransaction.str_id == order['payment_id']
            ).first()
            if txn.data['SERVICE'] == 'PAYTM':
                if 'RFID' in txn.data:
                    refund_res = self._check_refund_status(order['payment_id'], txn.data['RFID'])
                    if 'status' in refund_res and refund_res['status'] == 'failure':
                        return refund_res
                    if refund_res['RESPCODE'] != '10':
                        refund_txn = OnlineTransaction.query.filter(
                            OnlineTransaction.str_id == txn.data['RFID']
                        ).first()
                        refund_txn.is_active = False
                        pgdb.session.add(refund_txn)
                        pgdb.session.commit()
                refund_txn = OnlineTransaction()
                refund_txn.txn_type = "refund"
                txn.data['RFID'] = refund_txn.str_id
                pgdb.session.add(refund_txn)
                pgdb.session.add(txn)
                pgdb.session.commit()
                data = {
                    'amount': order['cash_collected'],
                    'refund_id': refund_txn.str_id,
                    'payment_id': order['payment_id'],
                    'order_id': str(order['_id']),
                    'txn_id': txn.data['TXNID']
                }
                return {'refund_data': data}
            return {'refund_data': None}
        except Exception as e:
            return {'status': 'failure', 'error': 'Unable to retrive refund status'}, 500

    def post(self):
        try:
            form = copy.deepcopy(request.form)
            if 'payment_id' not in form:
                return {'status': 'failure', 'error': 'payment_id not provided'}
            if 'order_id' not in form:
                return {'status': 'failure', 'error': 'order_id not provided'}
            if 'refund_id' not in form:
                return {'status': 'failure', 'error': 'refund_id not provided'}
            if 'txn_id' not in form:
                return {'status': 'failure', 'error': 'refund_id not provided'}
            if 'type' not in form:
                return {'status': 'failure', 'error': 'type not provided'}
            # elif 'type' in form and (form.get('type') != 'cancel' or form.get('type') != 'refund'):
            #     print form.get('type')
            #     return {'status': 'failure', 'error': 'invalid type provided'}
            order = db.orders.find_one({'_id': ObjectId(form.get('order_id'))})
            if 'refund_amount' not in form or float(order['cash_collected']) < float(form.get('refund_amount')):
                return {'status': 'failure', 'error': 'amount not provided'}
            refund_txn = OnlineTransaction.query.filter(
                OnlineTransaction.str_id == form.get('refund_id')
            ).first()
            json_data = {
                'MID': settings.PAYTM_CRED['mid'],
                'TXNID': form.get('txn_id'),
                'ORDERID': form.get('payment_id'),
                'TXNTYPE': form.get('type').upper(),
                'REFUNDAMOUNT': str(form.get('refund_amount')),
            }
            json_data['CHECKSUM'] = generate_checksum(json_data, settings.PAYTM_CRED['merchant_key'])
            try:
                json_data['REFID'] = form.get('refund_id')
                if 'comments' in form:
                    json_data['COMMENTS'] = form.get('comments')
                if 'comments' not in form:
                    encode_url = str('"MID":"%s","TXNID":"%s","ORDERID":"%s","REFUNDAMOUNT":"%s","TXNTYPE":"%s","REFID":"%s","CHECKSUM":"%s"' % (
                        json_data['MID'], json_data['TXNID'], json_data['ORDERID'],
                        json_data['REFUNDAMOUNT'], json_data['TXNTYPE'],
                        json_data['REFID'], json_data['CHECKSUM'])
                    )
                    encode_url = urllib.quote(encode_url.encode('utf-8'), safe='')
                    url = settings.PAYTM_REFUND + '?JsonData={%s}' % encode_url
                else:
                    encode_url = str('"MID":"%s","TXNID":"%s","ORDERID":"%s","REFUNDAMOUNT":"%s","TXNTYPE":"%s","COMMENTS":"%s","REFID":"%s","CHECKSUM":"%s"' % (
                        json_data['MID'], json_data['TXNID'], json_data['ORDERID'],
                        json_data['REFUNDAMOUNT'], json_data['TXNTYPE'], json_data['COMMENTS'],
                        json_data['REFID'], json_data['CHECKSUM'])
                    )
                    encode_url = urllib.quote(encode_url.encode('utf-8'), safe='')
                    url = settings.PAYTM_REFUND + '?JsonData={%s}' % encode_url
                res = requests.post(url)
            except Exception as e:
                print str(e)
                return {'status': 'failure', 'error': str(e)}

            refund_data = res.json()
            refund_data.pop('MID')
            data = {}
            refund_data['SERVICE'] = 'PAYTM'
            refund_txn.txn_type = form.get('type')
            data['refund_id'] = refund_data.pop('REFID')
            sms = None
            if refund_data['RESPCODE'] == '10':
                data['cash_collected'] = float(order['cash_collected']) - float(form.get('refund_amount'))
                data['is_paid'] = form.get('type')
                if 'TXNDATE' in refund_data:
                    txn_date = refund_data.pop('TXNDATE')
                    refund_txn.txn_date = datetime.strptime(
                        txn_date[:txn_date.index('.')],
                        '%Y-%m-%d %H:%M:%S'
                    )
                sms = "Greetings from MyWash ! Amount of Rs." + \
                    str(form.get('refund_amount')) + " is sucessfully refunded for order ID #" + order['order_id']
            # elif refund_data['STATUS'] == 'TXN_FAILURE' or refund_data['STATUS'] == 'TXN_PENDING':
            else:
                refund_txn.txn_date = datetime.now()
            refund_txn.data = refund_data
            try:
                pgdb.session.add(refund_txn)
                pgdb.session.commit()
                result = db.orders.update(
                    {'payment_id': form.get('payment_id')},
                    {'$set': data}
                )
                emails.mywash_order_transactional_sms(
                    order['phone'].strip(),
                    sms,
                    order.get('partner_id', None)
                )
                print result
                return {'status': 'success'}, 200
            except Exception, e:
                return {"status": "failure", "error": "db error"}, 500
        except Exception, e:
            return {"status": "failure", "error": "Payment refund Failed: " + str(e)}, 403
