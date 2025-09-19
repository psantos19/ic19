from pydantic import BaseModel
from typing import Any

class SignupIn(BaseModel):
    home_zone: str
    work_zone: str
    flex_minus_min: int = 0
    flex_plus_min: int = 0
    employer_name: str | None = None
    preferences_json: Any | None = None  # <— novo, opcional

class AcceptIn(BaseModel):
    user_id: int
    date: str
    slot_iso: str
