import os
import Constants
import requests
import geoip2.database
from database import conn

#DEBUG equals true if the env is local or testing system otherwise false ie.. production server
DEBUG = True if os.getenv('SERVER_TYPE') == "local" or os.getenv('SERVER_TYPE') == "staging" else False
IS_STAGING = True if os.getenv('SERVER_TYPE') == "staging" else False

#below gets the path of current directory
BASE_DIR = os.path.dirname(__file__)
DB_URI = ""

MAINTENANCE = False
MAINTENANCE_END = '1:00 am'

# Mongodb configuration and instantiation
#below settings are self explanatory if you can understand the above settings
mongo_host = None
if DEBUG:
    mongo_host = "172.31.28.170" if IS_STAGING else "localhost"
    redis_host = "172.31.28.170" if IS_STAGING else "localhost"
else:
    mongo_host = "172.31.24.50"
    redis_host = "172.31.28.114"

REDIS_CREDS = {
    'HOST': redis_host,
    'PORT': 6379,
    'DB': 1,
    'PASSWORD': None,
    'SEARCH_DB': 0,
    'SESSION_KEY': "session_",
    'KEY_PREFIX': "session_",
    'EXPIRE': 86400
}
REDIS_CLIENT = conn.redis_conn(REDIS_CREDS)

MONGO_CREDS = {
    'HOST': mongo_host,
    'USER': "" if DEBUG else "admin",
    "PASSWORD": "",
    "PORT": "27017",
}

DEFAULT_HOST_NAME = "/"

API_SERVER = {}

#the SECRET key variables are used for sessions as secret_key
if DEBUG:
    if IS_STAGING:
        FB_APP_ID = "1636285796601592"
        FB_APP_SECRET = "2b84da6dd44ced8ec3f2c869c5a6ded4"
        print "config is staging"
        API_SERVER['dashboard'] = "http://52.74.14.177"
        API_SERVER['private_dashboard'] = "http://172.31.27.244"
        WEBSITE = "http://ec2-52-74-236-50.ap-southeast-1.compute.amazonaws.com"
        GOOGLE_ID = "705039323534-osb8fdo3lnpc8v9ic0mrck939lt23085.apps.googleusercontent.com"
        GOOGLE_SECRET = "PMaF1-NokvdqZiGJ-Uiq-47r"
    else:
        FB_APP_ID = "265817303523220"
        FB_APP_SECRET = "f232d1c2d4ad995019c8bb12b9f92956"
        print "config is local"
        WEBSITE = "http://localhost:5000"
        API_SERVER['dashboard'] = "http://localhost:5000"
        API_SERVER['private_dashboard'] = "http://localhost:5000"
        GOOGLE_ID = "705039323534-jn71kdv2lvl98s9i6ejcnmiuf2g1t3ic.apps.googleusercontent.com"
        GOOGLE_SECRET = "BFBgPevhJk5iJkqF_z7gMFqA"
else:
    FB_APP_ID = "1541731196057053"
    FB_APP_SECRET = "1f232ba5f10fec07115406ed9bd82dcd"
    print "config is prod"
    WEBSITE = "http://www.mywash.in"
    API_SERVER['dashboard'] = "http://54.169.157.52"
    API_SERVER['private_dashboard'] = "http://172.31.25.90"
    GOOGLE_ID = "630971295845-ihjesvcrh0qduvc5dpv5i2r7ofn5rjig.apps.googleusercontent.com"
    GOOGLE_SECRET = "Xrg58bdAx08ElmN0OS2arfSl"

TWITTER_KEY = "4FFiQKOMhRkaAw40dOX6DsWkH"
TWITTER_SECRET = "soV7Q2CvB95mF9WhYwbTjZIJFtOKoMat787o6TSpaUPhpnccfa"

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
BUCKET_NAME = ""

GEOIPDB_LOCATION = BASE_DIR + '/geoip2/GeoLite2-City.mmdb'
GEOIPDB = geoip2.database.Reader(GEOIPDB_LOCATION)

# presently registered with a.prashanth18@gmail.com
NUDGESPOT_CREDS = {
    'URL_ACTIVITY': "https://api.nudgespot.com/activities",
    'USERNAME': "api",
    'API_KEY': "a7f206921fb32011a45c1e28331b3e8f"
}

NUDGESPOT_HEADER = {'Content-type': 'application/json', 'Accept': 'application/json'}

AWS_CREDS = {
    'bucket': 'mywash-invoices' if not DEBUG else 'invoice-staging'
}

if not DEBUG:
    SENDGRID_UNAME = "mywash"
    SENDGRID_PWD = "dummy123"

# TIMESLOTS = requests.request('GET', API_SERVER['dashboard'] + "/api/timeslot").json()['data']
TIMESLOTS = {"1": "8am - 10am", "3": "12pm - 2pm", "2": "10am - 12pm", "5": "4pm - 6pm", "4": "2pm - 4pm", "7": "8pm - 10pm", "6": "6pm - 8pm"}


