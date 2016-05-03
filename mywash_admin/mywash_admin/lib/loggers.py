from mywash_admin import settings
import logging
from datetime import datetime
import sys
import traceback

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
        data['status'] = logging.WARNING
        self._handler(message, data)

    def debug(self, message=None, **data):
        data['status'] = logging.DEBUG
        self._handler(message, data)

    def fatal(self, message=None, **data):
        data['status'] = logging.FATAL
        self._handler(message, data)

    def error(self, message=None, **data):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        data['status'] = logging.ERROR
        data['exception'] = repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        self._handler(message, data)

    def critical(self, message=None, **data):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        data['exception'] = repr(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        data['status'] = logging.CRITICAL
        self._handler(message, data)

    def info(self, message=None, **data):
        data['status'] = logging.INFO
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
        if self.collection.save(data) and self._print_log:
            self.display(data)


## WARNING: Do not use this logger, it's implementaion is still not complete
class MotorLogger(MongoLogger):
    # TODO: Making async calls, i.e. async insert
    def __init__(self, collection_name):
        self.db = settings.ASYNC_MONGO_CLIENT[settings.MONGO_CONF['NAME']['2']]
        self.collection = self.db[collection_name]


if __name__ == '__main__':
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'oneklik.settings'

    logger = MongoLogger("new_collection")
    logger.print_log = True
    logger.debug("This is my message")