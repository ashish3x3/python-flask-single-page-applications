import copy

from flask.ext.restful import Resource
from flask import request

from mywash_log.lib.loggers import MongoLogger


class Logger(Resource):
	def post(self):
		try:
			data = {}
			log_type = None
			message = None
			form = copy.deepcopy(request.form)
			# print '============================='
			# print form
			# print '============================='
			# print 'form.log_type..',form.get('log_type')

			logger = MongoLogger('mywash_logs', 'exception_logs')
			print 'form...',form


			if 'log_type' in form :
				# print '============================='


				# print 'inside iff'
				message = form.get('message')
				# print message
				log_type = form.get('log_type')
				# print log_type
				# print 'data..',form.get('data')
				# print '============================='

				# print 'data.exception..',form.get(data.exception)
				# print form.get(data.get('exception'))
				# print 'form.data...',form.get('data')

				# data = form.get('data')
				# print 'data,.....',data.request

				# logger = MongoLogger('mywash_logs', form.get('exception_logs'))
				# data['exception'] = form.get('data.exception', '')
				# data['instance'] = form.get('instance', '')
				# data['user_agent'] = form.get('data.request.user_agent', '')
				# data['status_code'] = form.get('status_code', '')
				# # data['request_query'] = form.get('request_query', '')
				# data['msg'] = form.get('data.msg', '')

				# print '============================='

				# print 'data["exception"]...',data['exception']
				# print 'data["user_agent"]..',data['user_agent']
				# print 'data["msg"]...',data['msg']
				# print '============================='

				if log_type == 'warning':
					logger.warning(form.get('message'),data=form)
				elif log_type == 'debug':
					logger.debug(form.get('message'),data=form)
				elif log_type == 'fatal':
					logger.fatal(form.get('message'),data=form)
				elif log_type == 'error':
					print 'logger.error called..'
					logger.error(form.get('message'),data=form)
				elif log_type == 'critical':
					print 'logger.critical'
					logger.critical(form.get('message'),data=form)
				else:
					logger.info(form)
				return {'status': "success"}
			else:
				return {'status': "failure", 'error': "no log_type / message provided"}
		except Exception as e:
			print 'exception........',str(e)
			return {'status': "failure", 'error': str(e)}
