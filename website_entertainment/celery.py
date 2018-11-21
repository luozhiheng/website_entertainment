from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website_entertainment.settings')

app = Celery('website_entertainment')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

"""
bind means the first argument to the task will always be the task instance (self)
Bound tasks are needed for retries (using app.Task.retry()), 
for accessing information about the current task request, 
and for any additional functionality you add to custom task base classes.
"""
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
