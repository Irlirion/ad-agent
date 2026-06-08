from datetime import datetime

from pydantic import BaseModel


class TelemetryPoint(BaseModel):
    timestamp: datetime
    value: float


class Segment(BaseModel):
    segment_id: str
    channel: str
    points: list[TelemetryPoint]
    sampling_rate: float | None = None
