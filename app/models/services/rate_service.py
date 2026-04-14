import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.models.rate import Rate
from app.models.repositories.rate_repository import RateRepository

logger = logging.getLogger(__name__)

DOLAR_API_URL = "https://dolarapi.com/v1/dolares"


class RateService:

    @staticmethod
    def fetch_and_store(db: Session) -> list[Rate]:
        try:
            response = httpx.get(DOLAR_API_URL, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.error("Failed to fetch rates: %s", exc)
            return []

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        rates = [
            Rate(
                type=item["casa"],
                name=item["nombre"],
                buy=item.get("compra"),
                sell=item["venta"],
                fetched_at=now,
            )
            for item in data
            if item.get("venta") is not None
        ]

        if rates:
            RateRepository.bulk_create(db, rates)
            logger.info("Stored %d rates at %s", len(rates), now)

        return rates

    @staticmethod
    def get_latest(db: Session) -> list[Rate]:
        return RateRepository.get_latest(db)

    @staticmethod
    def get_history(db: Session, rate_type: str | None, since: datetime | None, limit: int) -> list[Rate]:
        return RateRepository.get_history(db, rate_type=rate_type, since=since, limit=limit)

    @staticmethod
    def get_stats(db: Session, rate_type: str, since: datetime) -> dict:
        return RateRepository.get_stats(db, rate_type=rate_type, since=since)
