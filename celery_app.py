# fraud_detection/celery_app.py
from celery import Celery
import os

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery('fraud_detection', broker=broker_url, backend=broker_url)

# Autodiscover tasks in the tasks package
app.autodiscover_tasks(['fraud_detection.tasks'])
