from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, EmailStr, field_validator


class AlertCreate(BaseModel):
    email:         EmailStr
    rate_type:     str
    min_threshold: float | None = None
    max_threshold: float | None = None


class AlertResponse(BaseModel):
    id:            int
    email:         str
    rate_type:     str
    min_threshold: float | None
    max_threshold: float | None
    active:        bool
    last_alerted:  datetime | None
    created_at:    datetime

    model_config = {"from_attributes": True}

    @field_validator("created_at", "last_alerted", mode="before")
    @classmethod
    def assume_utc(cls, v: Any) -> Any:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
