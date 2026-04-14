from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

VALID_FREQUENCIES = ("hourly", "daily", "weekly")


class ReportConfig(Base):
    __tablename__ = "report_configs"

    id:          Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    email:       Mapped[str]            = mapped_column(String(255), nullable=False)
    frequency:   Mapped[str]            = mapped_column(String(20), nullable=False)  # hourly | daily | weekly
    active:      Mapped[bool]           = mapped_column(Boolean, default=True)
    last_sent:   Mapped[datetime | None]= mapped_column(DateTime, nullable=True)
    created_at:  Mapped[datetime]       = mapped_column(DateTime, default=datetime.utcnow)
