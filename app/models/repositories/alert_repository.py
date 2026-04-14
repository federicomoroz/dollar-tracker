from datetime import datetime

from sqlalchemy.orm import Session

from app.models.alert import AlertConfig


class AlertRepository:

    @staticmethod
    def create(db: Session, alert: AlertConfig) -> AlertConfig:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_all(db: Session) -> list[AlertConfig]:
        return db.query(AlertConfig).order_by(AlertConfig.created_at.desc()).all()

    @staticmethod
    def get_active(db: Session) -> list[AlertConfig]:
        return db.query(AlertConfig).filter(AlertConfig.active == True).all()

    @staticmethod
    def get_by_id(db: Session, alert_id: int) -> AlertConfig | None:
        return db.query(AlertConfig).filter(AlertConfig.id == alert_id).first()

    @staticmethod
    def update_last_alerted(db: Session, alert: AlertConfig, ts: datetime) -> None:
        alert.last_alerted = ts
        db.commit()

    @staticmethod
    def delete(db: Session, alert: AlertConfig) -> None:
        db.delete(alert)
        db.commit()
