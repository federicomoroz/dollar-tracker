from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.services.report_service import ReportService
from app.views.schemas.report import ReportCreate, ReportResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, status_code=201, summary="Subscribe to periodic reports")
def create_report(body: ReportCreate, db: Session = Depends(get_db)):
    return ReportService.create_report(db, email=str(body.email), frequency=body.frequency)


@router.get("", response_model=list[ReportResponse], summary="List all report subscriptions")
def list_reports(db: Session = Depends(get_db)):
    return ReportService.list_reports(db)


@router.delete("/{report_id}", status_code=204, summary="Delete a report subscription")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    if not ReportService.delete_report(db, report_id):
        raise HTTPException(status_code=404, detail=f"Report config {report_id} not found.")
