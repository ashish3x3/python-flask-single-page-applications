import os
from lib.database import conn
import googlemaps
from kombu import Queue

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = 'mywash_admin'

STAGING = True if os.environ.get("SERVER", None) == "staging" else False

ADMIN = {
    # 'phone': '8892020896',
    'phone': '8904590299',
    'email': 'tech@mywash.com'
}

if os.environ.get("SERVER", None) == "dev" or STAGING:
    DEBUG = True
else:
    DEBUG = False

# Serve the static files
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

# Serve static files through flask
STATIC_SERVE_URL = "/staticserve/"

SECRET_KEY = "1465d00a-ddc4-11e4-8be9-446d57ab6a83"

# Mongodb configuration and instantiation
mongo_host = None
if DEBUG:
    mongo_host = "172.31.28.170" if STAGING else "localhost"
    redis_host = "172.31.28.170" if STAGING else "localhost"
else:
    mongo_host = "172.31.24.50"
    redis_host = "172.31.28.114"

MONGO_CONF = {
    'USER': "",
    'PASSWORD': "",
    'HOST': mongo_host,
    'PORT': "27017",
    'DB': 0
}

MONGO_CLIENT = conn.mongo(MONGO_CONF)

REDIS_CREDS = {
    'HOST': redis_host,
    'PORT': 6379,
    'DB': 1,
    'PASSWORD': None
}

REDIS_CLIENT = conn.redis_conn(REDIS_CREDS)

DEFAULT_CLOTH_PIC = os.path.join(STATIC_ROOT, "core", "img", "items", "default.png")


if DEBUG:
    if STAGING:
        WEBSITE = "http://ec2-52-74-236-50.ap-southeast-1.compute.amazonaws.com"
    else:
        WEBSITE = "http://localhost:5001"
else:
    WEBSITE = "http://www.mywash.in"

if DEBUG and STAGING:
    print "Using staging db"
    API_SERVER = "52.74.14.177"
    SERVER_SELF = "http://0.0.0.0"
    POSTGRES_CONF = {
        'USER': "mywash",
        "PASSWORD": "dummy123",
        "HOST": "mywash-staging.cil2hfvth8qg.ap-southeast-1.rds.amazonaws.com",
        "PORT": "5432",
        "DB": "mywash_postgres",
        'MAX_CONN': 32,
        "STALE_TIMEOUT": 300
    }
    SQLALCHEMY_DATABASE_URI = "postgresql://" + POSTGRES_CONF['USER'] + ":" + POSTGRES_CONF['PASSWORD'] + "@" + POSTGRES_CONF['HOST'] + ":" + POSTGRES_CONF['PORT'] + "/" + POSTGRES_CONF['DB']
elif DEBUG:
    print "Using local db"
    API_SERVER = "localhost:5000"
    SERVER_SELF = "http://localhost:5000"
    POSTGRES_CONF = {
        'USER': "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "5432",
        "DB": "mywash_postgres",
        'MAX_CONN': 32,
        "STALE_TIMEOUT": 300
    }

    SQLALCHEMY_DATABASE_URI = "postgresql:///mywash_postgres"
else:
    print "Using prod db"
    API_SERVER = "54.169.157.52"
    SERVER_SELF = "http://0.0.0.0"
    POSTGRES_CONF = {
        'USER': "mywash",
        "PASSWORD": "553a868727e76e7f64d70e42",
        "HOST": "pstgresdb-prod-1.cil2hfvth8qg.ap-southeast-1.rds.amazonaws.com",
        "PORT": "5432",
        "DB": "mywash_postgres",
        'MAX_CONN': 32,
        "STALE_TIMEOUT": 300
    }
    SQLALCHEMY_DATABASE_URI = "postgresql://" + POSTGRES_CONF['USER'] + ":" + POSTGRES_CONF['PASSWORD'] + "@" + POSTGRES_CONF['HOST'] + ":" + POSTGRES_CONF['PORT'] + "/" + POSTGRES_CONF['DB']

SQLALCHEMY_POOL_SIZE = POSTGRES_CONF['MAX_CONN']
SQLALCHEMY_POOL_TIMEOUT = POSTGRES_CONF['STALE_TIMEOUT']

# if DEBUG:
TIMESLOTS = {"1": "8am - 10am", "3": "12pm - 2pm", "2": "10am - 12pm", "5": "4pm - 6pm", "4": "2pm - 4pm", "7": "8pm - 10pm", "6": "6pm - 8pm"}
# else:
#     TIMESLOTS = requests.request('GET', "http://" + API_SERVER + "/api/timeslot").json()['data']

ORDER_DICT = {
    "1": "Order Placed",
    "2": "Order Picked",
    "3": "Order Cleaned",
    "4": "Order Completed",
    "5": "Order Cancelled",
    "6": "Order Rejected"
}

DEPRECATED_STATUS_MAP = {
    1: 'order_placed',
    2: 'pickup_success',
    3: 'delivery_ready',
    4: 'clothes_delivered',
    5: 'order_cancelled',
    6: 'order_rejected',
}

SERVICE_TYPE_MAP = {
    "WASH & IRON": "laundry",
    "DRY_CLEANING": "dryclean",
    "IRON": "iron",
}

SERVICE_TYPE_DICT = {
    "WASH & IRON": "Wash & Iron",
    "DRY_CLEANING": "Dry Cleaning",
    "IRON": "Iron",
    "laundry": "Wash & Iron",
    "dryclean": "Dry Cleaning",
    "iron": "Iron",
}

SENDGRID_CONF = {
    'USER': "mywash",
    "PASSWORD": "dummy123"
}

# ozone, exotel
SMS_PROVIDER = 'solinifi'
SMS_CONF = None

if SMS_PROVIDER == 'exotel':
    SMS_CONF = {
        'SID': 'mywash',
        'TOKEN': 'c8bed8711ba94667d385418a6d3705828bb7884a'
    }

if SMS_PROVIDER == 'solinifi':
    SMS_CONF = {
        'SID': '',
        'TOKEN': ''
    }

if SMS_PROVIDER == 'ozone':
    SMS_CONF = {
        'SID': '2000145414',
        'TOKEN': 'chicken65'
    }


GOOGLE_MAPS_API = "AIzaSyDxb-2Wq3YsTU0l9Vx4NQyhW7pzD55qGpM"

GOOGLE_MAPS = googlemaps.Client(key=GOOGLE_MAPS_API)

GPLUS_CREDS = {
    'scopes': ['profile'],
    'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob'
}

EMPLOYEE_GPLUS_CREDS = {}

if DEBUG:
    GPLUS_CREDS['client_id'] = "205852036645-32166av5vp6nq39l7e4sk4q6vtcfd003.apps.googleusercontent.com"
    GPLUS_CREDS['client_secret'] = "FxyKsbt6ENNhHDgs6Ho4Sa2x"
    GPLUS_CREDS['android_client_id'] = '205852036645-rdfifgghm64a31atv84tte6o0h1ci24c.apps.googleusercontent.com'
    GPLUS_CREDS['api_key'] = 'AIzaSyB50dT6hyHKR-pFzYlhmbzMqOm0lorJNVI'

    EMPLOYEE_GPLUS_CREDS['client_id'] = "705039323534-9r0bkvberotntfev1ft7o1u1tlhvu94t.apps.googleusercontent.com"
    EMPLOYEE_GPLUS_CREDS['client_secret'] = "phJmG930Q2NN-nIT8ltAltKM"
else:
    GPLUS_CREDS['client_id'] = "1524168705-1v7hqel85pgpald5gi85hhp0oq0b7u1m.apps.googleusercontent.com"
    GPLUS_CREDS['client_secret'] = "5TPDOoLazA45cPkh9W9WL60V"
    GPLUS_CREDS['android_client_id'] = '1524168705-ps3cpvq1pgt4k2n7rv7c7lic5518b4qh.apps.googleusercontent.com'
    GPLUS_CREDS['api_key'] = 'AIzaSyC8n1kK594ky2qcns2w-h4d9EsqNF19n3s'

    EMPLOYEE_GPLUS_CREDS['client_id'] = "630971295845-7vrtso976ag0fno8d2pc8890sffdb573.apps.googleusercontent.com"
    EMPLOYEE_GPLUS_CREDS['client_secret'] = "0C16UDpp_Kh7-aO_LNAthOeT"


AWS_CREDS = {
    'access_key_id': 'AKIAIGHZKFZD6USMSLNA',
    'secret_access_key': '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',
    'bucket': 'mywash-invoices' if not DEBUG else 'invoice-staging',
    'bucket_reports': 'mywash-reports' if not DEBUG else 'invoice-staging',
    's3_uri': 'https://s3-ap-southeast-1.amazonaws.com'
}

PAYTM_CRED = {
    "mid": "Mywash21675342738992",
    "merchant_key": "N2#6&NUBKkmAyaFh",
    "industry_type_id": "Retail",
    "web": 'Mywash',
    "wap": 'mywashapp',
}

if DEBUG:
    PAYTM_TRX_URL = 'https://pguat.paytm.com/oltp-web/processTransaction?orderid='
    PAYTM_TXNSTATUS = 'https://pguat.paytm.com/oltp/HANDLER_INTERNAL/TXNSTATUS'
    PAYTM_REFUND = 'https://pguat.paytm.com/oltp/HANDLER_INTERNAL/REFUND'
    PAYTM_REFUND_STATUS = 'https://pguat.paytm.com/oltp/HANDLER_INTERNAL/REFUND_STATUS'
else:
    PAYTM_TRX_URL = 'https://secure.paytm.in/oltp-web/processTransaction?orderid='
    PAYTM_TXNSTATUS = 'https://secure.paytm.in/oltp/HANDLER_INTERNAL/TXNSTATUS'
    PAYTM_REFUND = 'https://secure.paytm.in/oltp/HANDLER_INTERNAL/REFUND'
    PAYTM_REFUND_STATUS = 'https://secure.paytm.in/oltp/HANDLER_INTERNAL/REFUND_STATUS'
    PAYTM_CRED = {
        "mid": "MyWash09878814925733",
        "merchant_key": "kMozZVquf@3g9QO_",
        "industry_type_id": "Retail115",
        "web": 'Mywashweb',
        "wap": 'Mywashwap',
    }


PARSE_CREDS = {"content_type": "application/json"}
if DEBUG:
    PARSE_CREDS['app_id'] = 'yXqFau0gdsr7uh1H0yiSFeoXCtk16Ht3UMSpgCfx'
    PARSE_CREDS['api_key'] = 'lxLkg0SNfIlFGiV3plIGDmV6GvS3u4SY22AMLQTy'
else:
    PARSE_CREDS['app_id'] = 'KMvztVq1GkhV4WUAQUp2RvYpMynFAY06jGlxbikF'
    PARSE_CREDS['api_key'] = 'cTBEg4R5J13ueObX452icUpnCzPCjzZ8qvr0mHhB'


class CeleryConfig(object):
    BROKER_URL = 'redis://%s:%s/5' % (REDIS_CREDS['HOST'], REDIS_CREDS['PORT'])
    CELERY_RESULT_BACKEND = 'redis://%s:%s/6' % (REDIS_CREDS['HOST'], REDIS_CREDS['PORT'])
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_DEFAULT_QUEUE = APP_NAME
    CELERY_QUEUES = (
        Queue(APP_NAME, routing_key=APP_NAME + '.#'),
    )
    CELERY_DEFAULT_EXCHANGE = 'tasks'
    CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
    CELERY_DEFAULT_ROUTING_KEY = 'celery.tasks'

CELERY_CONFIG = CeleryConfig


def update_redis_setting(hset, key, value):
    if not REDIS_CLIENT.hget(hset, key):
        REDIS_CLIENT.hset(hset, key, value)

update_redis_setting('SERVICE_TAX', 'type', 'exclusive')
update_redis_setting('SERVICE_TAX', 'rate', '14')

update_redis_setting('ANDROID_UPDATE', 'version', '1.9')
update_redis_setting('ANDROID_UPDATE', 'recommended', True)
update_redis_setting('ANDROID_UPDATE', 'mandatory', False)
update_redis_setting('ANDROID_UPDATE', 'min_supported_version', '1.8')

update_redis_setting('ANDROID_AGENT_UPDATE', 'version', '1.9')
update_redis_setting('ANDROID_AGENT_UPDATE', 'recommended', True)
update_redis_setting('ANDROID_AGENT_UPDATE', 'mandatory', False)
update_redis_setting('ANDROID_AGENT_UPDATE', 'min_supported_version', '1.8')


SENTRY_DSN = None
if DEBUG:
    SENTRY_DSN = 'http://02b980f9c847453ba626207a63dfebd6:d93138c1d41f42889b85da5113926e8d@ec2-54-255-201-33.ap-southeast-1.compute.amazonaws.com/2'
else:
    SENTRY_DSN = 'http://784b9411a2044ff2bc218a281563ee6e:d8fcd76442ad41f79cdd341744d0f7cc@ec2-54-254-211-192.ap-southeast-1.compute.amazonaws.com/2'