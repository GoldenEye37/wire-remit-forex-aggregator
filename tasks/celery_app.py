from celery import Celery

from app import create_app

# Create Flask app at module level so it's available to all tasks
flask_app = create_app()


def make_celery(app):
    """
    Create and configure a Celery instance with Flask app context.
    """
    try:
        # Logger is already configured by create_app()
        from loguru import logger

        celery = Celery(app.import_name)

        celery.config_from_object(
            {
                "broker_url": app.config.get(
                    "CELERY_BROKER_URL", "redis://localhost:6379/0"
                ),
                "result_backend": app.config.get(
                    "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
                ),
                "task_serializer": "json",
                "accept_content": ["json"],
                "result_serializer": "json",
                "timezone": "UTC",
                "enable_utc": True,
                "include": ["tasks.rate_refresh"],
                "beat_schedule": {
                    "refresh-rates-every-5min": {
                        "task": "tasks.rate_refresh.refresh_rates",
                        "schedule": 300.0,  # Every 5 minutes for testing
                    },
                },
            }
        )

        class ContextTask(celery.Task):
            """Custom task class that ensures Flask app context is available."""

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return super().__call__(*args, **kwargs)

        celery.Task = ContextTask

        logger.info(
            "Celery initialized",
            broker_url=app.config.get("CELERY_BROKER_URL"),
            beat_schedule_count=len(celery.conf.beat_schedule),
            service_name=app.config.get("OTEL_SERVICE_NAME"),
        )
        return celery
    except Exception as e:
        from loguru import logger

        logger.error(
            "Failed to initialize Celery", error=str(e), error_type=type(e).__name__
        )
        raise


celery = make_celery(flask_app)
