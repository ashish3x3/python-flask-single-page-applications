import os
from kombu import Queue
from celery import Celery

class CeleryConfig(object):
    BROKER_URL = 'redis://localhost:6379/5'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/6'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_DEFAULT_QUEUE = 'celery'
    CELERY_QUEUES = (
     Queue('celery',routing_key='celery.#'),
    )
    CELERY_ROUTES = {
        "facebook_app.celery_app.tasks.save_into_spinx_new" : {"queue":"searchindex", "routing_key":"searchindex.saveintospinxnew"},
        "facebook_app.celery_app.tasks.insta_data_index" : {"queue":"instaindex", "routing_key":"instaindex.instadataindex"},
        "facebook_app.controllers.naukri_job_management.handle_job_for_posting_and_tracking" : {"queue":"naukriposting", "routing_key":"naukriposting.handlenaukriposting"}
    }
    CELERY_DEFAULT_EXCHANGE = 'tasks'
    CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
    CELERY_DEFAULT_ROUTING_KEY = 'celery.tasks'

class ProductionCeleryConfig(CeleryConfig):
    BROKER_URL = 'redis://localhost:6379/5'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/6'



celeryConfig=ProductionCeleryConfig()

celery = Celery('boiler.controllers.sms',include=['boiler.controllers.sms','boiler.controllers.emails','boiler.service.nudgespot'])
celery.config_from_object(celeryConfig)
