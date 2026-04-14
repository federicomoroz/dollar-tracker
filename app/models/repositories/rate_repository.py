from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.rate import Rate


class RateRepository:

    @staticmethod
    def bulk_create(db: Session, rates: list[Rate]) -> None:
        db.add_all(rates)
        db.commit()

    @staticmethod
    def get_latest(db: Session) -> list[Rate]:
        subq = (
            db.query(Rate.type, func.max(Rate.fetched_at).label("max_at"))
            .group_by(Rate.type)
            .subquery()
        )
        return (
            db.query(Rate)
            .join(subq, (Rate.type == subq.c.type) & (Rate.fetched_at == subq.c.max_at))
            .order_by(Rate.type)
            .all()
        )

    @staticmethod
    def get_history(
        db: Session,
        rate_type: str | None = None,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[Rate]:
        q = db.query(Rate)
        if rate_type:
            q = q.filter(Rate.type == rate_type)
        if since:
            q = q.filter(Rate.fetched_at >= since)
        return q.order_by(Rate.fetched_at.desc()).limit(limit).all()

    @staticmethod
    def get_stats(db: Session, rate_type: str, since: datetime) -> dict:
        row = (
            db.query(
                func.min(Rate.sell).label("min_sell"),
                func.max(Rate.sell).label("max_sell"),
                func.avg(Rate.sell).label("avg_sell"),
                func.count(Rate.id).label("samples"),
            )
            .filter(Rate.type == rate_type, Rate.fetched_at >= since)
            .first()
        )
        return {
            "min_sell": round(row.min_sell, 2) if row.min_sell else None,
            "max_sell": round(row.max_sell, 2) if row.max_sell else None,
            "avg_sell": round(row.avg_sell, 2) if row.avg_sell else None,
            "samples":  row.samples,
        }
