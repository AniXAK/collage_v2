from celery import Celery


celery = Celery(
    'image_process',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

import tasksv2
