from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.services.alert_service import AlertService
from app.views.schemas.alert import AlertCreate, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("", response_model=AlertResponse, status_code=201, summary="Create a threshold alert")
def create_alert(body: AlertCreate, db: Session = Depends(get_db)):
    if body.min_threshold is None and body.max_threshold is None:
        raise HTTPException(status_code=422, detail="At least one threshold (min or max) is required.")
    return AlertService.create_alert(
        db,
        email=str(body.email),
        rate_type=body.rate_type,
        min_threshold=body.min_threshold,
        max_threshold=body.max_threshold,
    )


@router.get("", response_model=list[AlertResponse], summary="List all alerts")
def list_alerts(db: Session = Depends(get_db)):
    return AlertService.list_alerts(db)


@router.delete("/{alert_id}", status_code=204, summary="Delete an alert")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    if not AlertService.delete_alert(db, alert_id):
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found.")
