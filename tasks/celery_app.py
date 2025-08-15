from celery import Celery
from loguru import logger

from app import create_app


def make_celery():
    """
    Create and configure a Celery instance.
    """
    try:
        flask_app = create_app()

        celery = Celery(flask_app.import_name)

        celery.config_from_object(
            {
                "broker_url": flask_app.config.get(
                    "CELERY_BROKER_URL", "redis://localhost:6379/0"
                ),
                "result_backend": flask_app.config.get(
                    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
                ),
                "task_serializer": "json",
                "accept_content": ["json"],
                "result_serializer": "json",
                "timezone": "UTC",
                "enable_utc": True,
                "include": ["tasks.rate_refresh"],
                "beat_schedule": {
                    "refresh-rates-every-hour": {
                        "task": "tasks.rate_refresh.refresh_rates",
                        "schedule": 3600.0,  # Every hour
                    },
                },
            }
        )

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with flask_app.app_context():
                    return super().__call__(*args, **kwargs)

        celery.Task = ContextTask
        logger.info("Celery initialized")
        return celery
    except Exception as e:
        logger.error(f"Failed to initialize Celery: {e}")
        raise


celery = make_celery()
