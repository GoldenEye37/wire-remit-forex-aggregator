# Rate refresh task
from tasks.celery_app import celery


@celery.task
def refresh_rates():
    return "Test task executed successfully!"