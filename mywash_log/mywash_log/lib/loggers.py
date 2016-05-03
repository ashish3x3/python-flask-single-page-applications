import logging
import sys
import os
import traceback

from datetime import datetime

from mywash_log import settings
import json

LOGGING_STATUS = {
    logging.WARNING: "WARNING",
    logging.DEBUG: 'DEBUG',
    logging.FATAL: 'FATAL',
    logging.ERROR: 'ERROR',
    logging.CRITICAL: 'CRITICAL',
    logging.INFO: 'INFO'
}


class BaseLogger(object):
    _print_log = False

    def __init__(self):
        super(BaseLogger, self).__init__()

    @property
    def print_log(self):
        return self._print_log

    @print_log.setter
    def print_log(self, value):
        if str(type(value)).find("bool") == -1:
            raise TypeError("Value must be either True or False.")
        self._print_log = value

    def warning(self, message=None, **data):
        self._handler(message, data)

    def debug(self, message=None, **data):
        self._handler(message, data)

    def fatal(self, message=None, **data):
        self._handler(message, data)

    def error(self, message=None, **data):
        # print '================================================'
        # print 'message...',message
        # print 'data in error logger.py....',data
        # # for key, value in data.iteritems():
        # #     print "%s = %s" % (key, value)
        # print '================================================'

        self._handler(message, data)

    def critical(self, message=None, **data):
        self._handler(message, data)

    def info(self, message=None, **data):
        self._handler(message, data)

    def _handler(self, message, data):
        data['timestamp'] = datetime.utcnow()
        if message is not None:
            data['message'] = message
        self.log_handler(data)

    def log_handler(self, data):
        if self._print_log:
            self.display(data)

    def display(self, data):
        print "\n%s: %s" % (LOGGING_STATUS[data['status']], data['timestamp'])
        for key, value in data.iteritems():
            print "\t%s - %s" % (key, value)
        print "\n"


class MongoLogger(BaseLogger):
    collection = None

    def __init__(self, db, collection_name):
        super(MongoLogger, self).__init__()
        self.db = settings.MONGO_CLIENT[db]
        self.collection = self.db[collection_name]

    def log_handler(self, data):
        print '================================================'

        # print 'data in log handler....service..',data
        # print 'data.message..######',data['message']
        # print 'data.data..#############',data['data']
        d =  data['data']
        self.myprint(d)
        # for key,val in data['data'].items():
        #     if isinstance(val, dict):
        #         self.myprint(v)
        #     else:
        #         print key, "=>", val
            # if key == 'data':
            #     print '######## key  === data...##########'
            #     new_data = data['data']['data']
            #     print 'new data..',new_data
            #     # for key,val in new_data:
            #     #     print key, "=>", val
            #     print(json.dumps(new_data, indent=4))

        print '================================================'


        if self.collection.save(data) and self._print_log:
            self.display(data)

    def myprint(self,d):
        for k, v in d.iteritems():
            print k, "=>", v  
            # print 'type ######### of v...', type(v)
            # if isinstance(k, dict):
            #     print 'type ######### of v...dict..', type(v)
            #     self.myprint(v)
            # if isinstance(v, list):
            #     print 'type ######### of v list...', type(v)
            #     self.myprint(v)

            # if isinstance(v, tuple):
            #     print 'type ######### of v..tuple.', type(v)
            #     self.myprint(v)
            # if isinstance(v, unicode):
            #     print 'type ######### of v..unicode...', type(v)
            #     print k, "=>", v 
            # else:
            #     print 'else....'
            #     print k, "=>", v   


