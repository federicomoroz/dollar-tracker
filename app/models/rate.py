from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Rate(Base):
    __tablename__ = "rates"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, autoincrement=True)
    type:       Mapped[str]      = mapped_column(String(50), nullable=False)
    name:       Mapped[str]      = mapped_column(String(100), nullable=False)
    buy:        Mapped[float]    = mapped_column(Float, nullable=True)
    sell:       Mapped[float]    = mapped_column(Float, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_rates_type_fetched", "type", "fetched_at"),
    )
