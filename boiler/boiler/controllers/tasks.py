from celery import Celery

celery = Celery('tasks', broker="redis://localhost:6379/5")

@celery.task(name='tasks.add')
def add(x, y):
    print "inside celery task"
    return x + y

