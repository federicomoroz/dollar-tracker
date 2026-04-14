from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, field_validator


class RateResponse(BaseModel):
    id:         int
    type:       str
    name:       str
    buy:        float | None
    sell:       float
    fetched_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("fetched_at", mode="before")
    @classmethod
    def assume_utc(cls, v: Any) -> Any:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class StatsResponse(BaseModel):
    rate_type: str
    period:    str
    min_sell:  float | None
    max_sell:  float | None
    avg_sell:  float | None
    samples:   int
