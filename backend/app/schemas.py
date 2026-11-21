"""Request bodies with validation (pydantic returns HTTP 422 with the failing field for anything outside these limits)."""
from typing import Annotated, Literal
from pydantic import BaseModel, Field

HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"
Username = Annotated[str, Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.\-]+$")]
Time = Annotated[str, Field(pattern=HHMM)]

class Login(BaseModel): username: Annotated[str, Field(min_length=1, max_length=64)]; password: Annotated[str, Field(min_length=1, max_length=128)]

class LangIn(BaseModel): lang: Annotated[str, Field(min_length=2, max_length=8)]

class NewUser(BaseModel):
    username: Username; password: Annotated[str, Field(min_length=8, max_length=128)]
    telegram_chat_id: Annotated[str, Field(max_length=64)] | None = None; email: Annotated[str, Field(max_length=200, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")] | None = None

class NewElderly(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]; age: Annotated[int, Field(ge=0, le=120)] | None = None
    baseline_activity: Annotated[float, Field(ge=0, le=1000)] = 50; checkin_time: Time = "09:00"
    caregiver_id: int | None = None; emergency_contact: Annotated[str, Field(max_length=200)] = ""

class NewEvent(BaseModel): elderly_id: int; kind: Literal["activity", "fall", "ok", "sos"]; value: Annotated[float, Field(ge=0, le=1000)] = 0

class NewItem(BaseModel):
    kind: Literal["medication", "meal", "water", "activity"]; title: Annotated[str, Field(min_length=1, max_length=100)]; time: Time; note: Annotated[str, Field(max_length=300)] = ""

class Assign(BaseModel): caregiver_id: int | None = None

class Pose(BaseModel):
    elderly_id: int; keypoints: dict[str, list[float]]
    prev_keypoints: dict[str, list[float]] | None = None; dt_s: Annotated[float, Field(gt=0, le=60)] | None = None

class AccelWindow(BaseModel):
    elderly_id: int; window: list[list[float]]; fs: Annotated[int, Field(ge=1, le=1000)] = 50
