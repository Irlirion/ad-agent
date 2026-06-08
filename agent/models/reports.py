from typing import Literal

from pydantic import BaseModel

from agent.models.pyod_report import PyodReport

Method = Literal["profile", "spikes", "shifts", "ranges", "pyod"]


class DataProfile(BaseModel):
    stationarity_pvalue: float
    is_stationary: bool
    missing_ratio: float
    sampling_regularity: float
    noise_std: float
    is_normal: bool
    trend_direction: Literal["up", "down", "flat"]
    segment_length: int
    value_range: tuple[float, float]


class SpikeReport(BaseModel):
    spike_count: int
    spike_indices: list[int]
    spike_magnitudes: list[float]
    upper_threshold: float
    lower_threshold: float


class TrendShiftReport(BaseModel):
    shift_count: int
    shift_points: list[int]
    directions: list[Literal["up", "down"]]


class RangeViolationReport(BaseModel):
    channel_min: float
    channel_max: float
    violations: list[dict]


class SegmentAnalysis(BaseModel):
    segment_id: str
    is_anomaly: bool
    confidence: float
    reasoning: str
    supporting_evidence: list[str]


class AnomalyFinding(BaseModel):
    channel: str
    timestamp: str
    composite_score: float
    spike_count: int
    shift_count: int
    range_violations: int
    is_stationary: bool
    trend_direction: Literal["up", "down", "flat"]
    evidence: list[str]


class ChannelSummary(BaseModel):
    channel: str
    windows_checked: int
    anomalous_windows: int
    max_anomaly_score: float
    status: Literal["normal", "watch", "anomalous"]


class DailyReport(BaseModel):
    date: str
    channels_checked: int
    total_windows: int
    anomalous_windows: int
    overall_severity: Literal["green", "yellow", "red"]
    channel_summaries: list[ChannelSummary]
    top_anomalies: list[AnomalyFinding]


class AnomalousHoursReport(BaseModel):
    date: str
    channel: str | None
    total_hours_checked: int
    anomalous_hours: int
    findings: list[AnomalyFinding]


class TelemetrySegment(BaseModel):
    channel: str
    start_time: str
    end_time: str
    timestamps: list[str]
    values: list[float]
    n_points: int
    warning: str | None = None


class AnalysisReport(BaseModel):
    channel: str
    start_time: str
    end_time: str
    methods_run: list[Method]
    profile: DataProfile | None = None
    spikes: SpikeReport | None = None
    shifts: TrendShiftReport | None = None
    ranges: RangeViolationReport | None = None
    pyod: PyodReport | None = None
    warnings: list[str] = []


class ComparisonReport(BaseModel):
    windows: list[AnalysisReport]
    methods: list[Method]
    correlation: float | None = None
    channels_agree: bool = True
