from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, field_validator


class ReportCreate(BaseModel):
    email:     EmailStr
    frequency: Literal["hourly", "daily", "weekly"]


class ReportResponse(BaseModel):
    id:         int
    email:      str
    frequency:  str
    active:     bool
    last_sent:  datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("created_at", "last_sent", mode="before")
    @classmethod
    def assume_utc(cls, v: Any) -> Any:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
