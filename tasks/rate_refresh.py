import time

from loguru import logger

from app.services.rate_processor import RateProcessorService
from tasks.celery_app import celery


@celery.task(name="tasks.rate_refresh.refresh_rates", bind=True)
def refresh_rates(self):
    """
    Fetch rates from all configured providers for active currency pairs,
    save into the Rate table, and aggregate into AggregatedRate.
    """
    start_time = time.time()
    task_id = self.request.id

    logger.info(
        "Starting rate refresh task", task_id=task_id, task_name="refresh_rates"
    )

    try:
        processor = RateProcessorService()
        result = processor.process_rates_for_currencies()

        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            "Completed rate refresh task",
            task_id=task_id,
            task_name="refresh_rates",
            duration_ms=round(duration_ms, 2),
            status="success",
            result=result,
        )

        return result or {"status": "success"}
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        logger.error(
            "Rate refresh task failed",
            task_id=task_id,
            task_name="refresh_rates",
            duration_ms=round(duration_ms, 2),
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        raise
