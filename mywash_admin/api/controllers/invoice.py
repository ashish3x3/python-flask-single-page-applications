import bson
import json
import boto
import copy
import weasyprint
from datetime import datetime
from boto.s3.key import Key
from flask.ext.restful import Resource
from flask import jsonify, request
from flask import render_template
from mywash_admin import app
from mywash_admin.lib import utils, emails
from api.controllers.items import OrderItems


db = app.config['MONGO_CLIENT']['dealsup']

redis_client = app.config['REDIS_CLIENT']


class Invoice(Resource):
    def get(self, order_id):
        try:
            data = db.orders.find_one({"_id": bson.ObjectId(order_id)}, {"invoice": 1})
        except Exception:
            return {'status': 'failure', 'error': 'db error.'}, 500
        final_data = {}
        if 'invoice' in data:
            final_data['data'] = data['invoice'][-1]['data']
            final_data['customer_details'] = data['invoice'][-1]['customer_details']
        return jsonify({'data': final_data})


class InvoiceSendToCustomer(Resource):
    def post(self):
        form = copy.deepcopy(request.form)
        if 'order_id' not in form:
            return {'status': 'failure', 'error': 'order id not provided'}, 403
        order_id = form['order_id']
        try:
            data = db.orders.find_one({"_id": bson.ObjectId(order_id)}, {"invoice": 1})
        except Exception:
            return {'status': 'failure', 'error': 'db error.'}, 500

        if not data:
            return {'status': 'failure', 'error': 'order not found'}, 403

        items = OrderItems()
        invoice_data = json.loads(items.get(order_id).response[0])
        invoice_data['current_date'] = datetime.now().strftime("%Y-%m-%d")
        if app.config['DEBUG']:
            invoice_data['image_server'] = "https://s3-ap-southeast-1.amazonaws.com/invoice-staging/mywash-logo-sans-in-small.png"
        else:
            invoice_data['image_server'] = "http://" + app.config['API_SERVER'] + "/static/core/img/mywash-logo-sans-in-small.png"
        customer_email = invoice_data['customer_details']['user'].get('email', '').strip()
        customer_name = invoice_data['customer_details']['user'].get('name', '').strip()
        customer_phone = invoice_data['customer_details']['user'].get('phone', '').strip()

        invoice_data['pay_now'] = app.config['WEBSITE'] + '/getstatus/' + order_id
        html = render_template("emails/invoice.html", **invoice_data)
        if customer_email:
            emails.sendmail.delay(
                recepients='tech@mywash.com' if app.config['DEBUG'] else customer_email,
                recepientName="Tech team" if app.config['DEBUG'] else customer_name,
                senderMail='tech@mywash.com' if app.config['DEBUG'] else "team@mywash.com",
                subject="Your Invoice for Order #%s" % invoice_data['customer_details']['order_id'],
                html=html
            )

        partner_id = data.get('user', {}).get('partner_id', None)
        if customer_phone and \
                ('is_paid' not in invoice_data['customer_details'] or
                    invoice_data['customer_details']['is_paid'] != 'paid'):
            text = "Your invoice amount for OrderId #%(order_id)s is INR %(amount)s.%(frag)s Thanks for using MyWash." % {
                'order_id': invoice_data['customer_details']['order_id'],
                'amount': invoice_data['customer_details']['cost']['total'],
                'frag': " Check mail for details." if customer_email else ''
            }
            emails.mywash_order_transactional_sms(
                app.config['ADMIN']['phone'] if app.config['DEBUG'] else customer_phone,
                text,
                partner_id
            )
        return {'status': 'success'}


class InvoiceIntoDrive(Resource):

    def _upload_to_s3(self, aws_access_key_id, aws_secret_access_key, file, bucket, key):
        try:
            conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
            bucket = conn.get_bucket(bucket, validate=False)
            k = Key(bucket)
            k.key = key
            k.content_type = "application/pdf"
            k.set_contents_from_file(file)
            k.set_acl('public-read')
            return True
        except Exception as e:
            print str(e)
            return False

    def post(self, order_id):
        try:
            try:
                data = db.orders.find_one({"_id": bson.ObjectId(order_id)}, {"invoice": 1, 'order_id': 1})
            except Exception:
                return {'status': 'failure', 'error': 'db error.'}, 500

            if not data:
                return {'status': 'failure', 'error': 'order not found'}, 403
            items = OrderItems()
            invoice_data = json.loads(items.get(order_id).response[0])
            invoice_data['current_date'] = datetime.now().strftime("%Y-%m-%d")
            if app.config['DEBUG']:
                invoice_data['image_server'] = "https://s3-ap-southeast-1.amazonaws.com/invoice-staging/mywash-logo-sans-in-small.png"
            else:
                invoice_data['image_server'] = "http://" + app.config['API_SERVER'] + "/static/core/img/mywash-logo-sans-in-small.png"
            try:
                html = render_template("emails/invoice.html", **invoice_data)
                fp = weasyprint.HTML(string=html).write_pdf()
                if not self._upload_to_s3(
                    app.config['AWS_CREDS']['access_key_id'],
                    app.config['AWS_CREDS']['secret_access_key'],
                    fp,
                    app.config['AWS_CREDS']['bucket'],
                    data['order_id'] + ".pdf"
                ):
                    return {'status': 'failure', 'error': 's3 error'}, 403
            except Exception as e:
                return {'status': 'failure', 'error': 'pdf error'}, 403
        except Exception, e:
            print str(e)
            return {'status': 'failure', 'error': 'db error'}, 403

        return {'status': 'success'}
