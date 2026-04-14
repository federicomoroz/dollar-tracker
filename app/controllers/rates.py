from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.services.rate_service import RateService
from app.views.schemas.rate import RateResponse, StatsResponse

router = APIRouter(prefix="/rates", tags=["Rates"])


@router.get("/current", response_model=list[RateResponse], summary="Latest rate for each type")
def get_current(db: Session = Depends(get_db)):
    return RateService.get_latest(db)


@router.get("/history", response_model=list[RateResponse], summary="Historical rates")
def get_history(
    type:  str | None = Query(None, description="Filter by rate type (e.g. blue, oficial)"),
    days:  int        = Query(1, ge=1, le=90, description="How many days back"),
    limit: int        = Query(200, ge=1, le=1000),
    db:    Session    = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    return RateService.get_history(db, rate_type=type, since=since, limit=limit)


@router.get("/stats", response_model=StatsResponse, summary="Min/max/avg for a rate type")
def get_stats(
    type: str = Query(..., description="Rate type (e.g. blue, oficial)"),
    days: int = Query(1, ge=1, le=90),
    db:   Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    stats = RateService.get_stats(db, rate_type=type, since=since)
    return StatsResponse(
        rate_type=type,
        period=f"last {days}d",
        **stats,
    )


@router.post("/fetch", response_model=list[RateResponse], summary="Manually trigger a rate fetch")
def manual_fetch(db: Session = Depends(get_db)):
    return RateService.fetch_and_store(db)
