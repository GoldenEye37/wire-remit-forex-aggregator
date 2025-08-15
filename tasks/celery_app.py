from celery import Celery
from loguru import logger

from app import create_app


def make_celery():
    """
    Create and configure a Celery instance.
    """
    try:
        flask_app = create_app()

        celery = Celery(
            flask_app.import_name,
            broker=flask_app.config["CELERY_BROKER_URL"],
            backend=flask_app.config["CELERY_RESULT_BACKEND"],
            include=["tasks.rate_refresh"],
        )
        celery.conf.update(flask_app.config)

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