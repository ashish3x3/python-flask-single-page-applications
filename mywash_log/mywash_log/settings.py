import os
from lib.database import conn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_NAME = 'mywash_logs'

STAGING = True if os.environ.get("SERVER", None) == "staging" else False

DEBUG = True if os.environ.get("SERVER", None) == "dev" or STAGING else False



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

if DEBUG:
    if STAGING:
        print "config is staging"
        API_SERVER = ""
        WEBSITE = "http://ec2-52-74-236-50.ap-southeast-1.compute.amazonaws.com"
    else:
        print "config is local"
        API_SERVER = ""
        WEBSITE = "http://localhost:5000"
else:
    print "config is prod"
    API_SERVER = "http://54.169.157.52"
    WEBSITE = "http://www.mywash.in"


if DEBUG and STAGING:
    print "Using staging db"
    API_SERVER = "52.74.14.177"
    LOGGER = "http://54.255.188.117:5003"
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
    LOGGER = "http://localhost:5003"
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
