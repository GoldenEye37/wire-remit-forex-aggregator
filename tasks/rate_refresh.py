from loguru import logger

from app.services.rate_processor import RateProcessorService
from tasks.celery_app import celery


@celery.task(name="tasks.rate_refresh.refresh_rates", bind=True)
def refresh_rates():
    """
    Fetch rates from all configured providers for active currency pairs,
    save into the Rate table, and aggregate into AggregatedRate.
    """
    logger.info("Starting refresh_rates task")
    try:
        processor = RateProcessorService()
        result = processor.process_rates_for_currencies()
        logger.info("Completed refresh_rates task")
        return result or {"status": "success"}
    except Exception as e:
        logger.exception(f"refresh_rates task failed: {e}")
        raise
