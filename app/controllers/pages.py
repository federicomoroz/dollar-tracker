from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.services.rate_service import RateService
from app.views.templates.landing import render_landing

router = APIRouter(tags=["Pages"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing(db: Session = Depends(get_db)):
    rates = RateService.get_latest(db)
    return render_landing(rates)
