from pydantic import BaseModel


class PyodReport(BaseModel):
    channel: str
    start_time: str
    end_time: str
    detector: str
    window_size: int
    n_timestamps: int
    n_anomalies: int
    anomaly_indices: list[int]
    anomaly_timestamps: list[str]
    anomaly_scores: list[float]
    mean_score: float
    max_score: float
    threshold: float
