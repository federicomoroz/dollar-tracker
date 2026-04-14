import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import FETCH_INTERVAL_MINUTES
from app.core.database import SessionLocal
from app.models.services.alert_service import AlertService
from app.models.services.rate_service import RateService
from app.models.services.report_service import ReportService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _fetch_job() -> None:
    logger.info("Scheduler: fetching rates...")
    db = SessionLocal()
    try:
        rates = RateService.fetch_and_store(db)
        if rates:
            AlertService.check_and_notify(db, rates)
            ReportService.send_due_reports(db)
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        _fetch_job,
        trigger="interval",
        minutes=FETCH_INTERVAL_MINUTES,
        id="fetch_rates",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — interval: %d min", FETCH_INTERVAL_MINUTES)


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
