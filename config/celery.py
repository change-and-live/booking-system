import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

if os.name == 'nt':
    app.conf.update(
        worker_pool='solo',
        worker_cancel_long_running_tasks_on_connection_loss=True
    )