from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id:            Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:         Mapped[str]            = mapped_column(String(255), nullable=False)
    rate_type:     Mapped[str]            = mapped_column(String(50), nullable=False)
    min_threshold: Mapped[float | None]   = mapped_column(Float, nullable=True)
    max_threshold: Mapped[float | None]   = mapped_column(Float, nullable=True)
    active:        Mapped[bool]           = mapped_column(Boolean, default=True)
    last_alerted:  Mapped[datetime | None]= mapped_column(DateTime, nullable=True)
    created_at:    Mapped[datetime]       = mapped_column(DateTime, default=datetime.utcnow)
