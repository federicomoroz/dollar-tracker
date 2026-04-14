from datetime import datetime

from sqlalchemy.orm import Session

from app.models.report import ReportConfig


class ReportRepository:

    @staticmethod
    def create(db: Session, report: ReportConfig) -> ReportConfig:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_all(db: Session) -> list[ReportConfig]:
        return db.query(ReportConfig).order_by(ReportConfig.created_at.desc()).all()

    @staticmethod
    def get_active(db: Session) -> list[ReportConfig]:
        return db.query(ReportConfig).filter(ReportConfig.active == True).all()

    @staticmethod
    def get_by_id(db: Session, report_id: int) -> ReportConfig | None:
        return db.query(ReportConfig).filter(ReportConfig.id == report_id).first()

    @staticmethod
    def update_last_sent(db: Session, report: ReportConfig, ts: datetime) -> None:
        report.last_sent = ts
        db.commit()

    @staticmethod
    def delete(db: Session, report: ReportConfig) -> None:
        db.delete(report)
        db.commit()
