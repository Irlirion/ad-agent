from datetime import datetime
from typing import Annotated, Literal

import numpy as np
from langchain_core.tools import tool
from pydantic import Field
from scipy import signal

from agent.models.pyod_report import PyodReport
from agent.models.reports import (
    AnalysisReport,
    DataProfile,
    Method,
    RangeViolationReport,
    SpikeReport,
    TrendShiftReport,
)
from agent.tools.channel_profiles import NOMINAL_RANGES
from agent.tools.data_loader import load_telemetry_range

PyodDetector = Literal["IForest", "HBOS", "KNN", "LOF", "PCA", "OCSVM"]
ScoreAggregation = Literal["max", "mean"]


def detect_spikes_mad(
    values: np.ndarray,
    threshold: float = 3.5,
) -> SpikeReport:
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    if mad == 0:
        return SpikeReport(
            spike_count=0,
            spike_indices=[],
            spike_magnitudes=[],
            upper_threshold=float(median),
            lower_threshold=float(median),
        )

    modified_z = 0.6745 * (values - median) / mad
    upper = float(median + threshold * (mad / 0.6745))
    lower = float(median - threshold * (mad / 0.6745))

    peaks, _ = signal.find_peaks(values, prominence=mad)
    troughs, _ = signal.find_peaks(-values, prominence=mad)

    indices: list[int] = []
    magnitudes: list[float] = []
    for idx in peaks:
        if modified_z[idx] > threshold:
            indices.append(int(idx))
            magnitudes.append(float(values[idx]))
    for idx in troughs:
        if modified_z[idx] < -threshold:
            indices.append(int(idx))
            magnitudes.append(float(values[idx]))

    return SpikeReport(
        spike_count=len(indices),
        spike_indices=indices,
        spike_magnitudes=magnitudes,
        upper_threshold=upper,
        lower_threshold=lower,
    )


def detect_shifts_cusum(
    values: np.ndarray,
    decision_threshold: float = 5.0,
    drift: float = 0.25,
) -> TrendShiftReport:
    n = len(values)
    if n < 15:
        return TrendShiftReport(shift_count=0, shift_points=[], directions=[])

    mean = np.mean(values)
    std = np.std(values)
    if std == 0:
        return TrendShiftReport(shift_count=0, shift_points=[], directions=[])

    k = drift * std
    h = decision_threshold * std
    s_high = 0.0
    s_low = 0.0
    shift_points: list[int] = []
    directions: list[str] = []

    for i in range(n):
        s_high = max(0, s_high + (values[i] - mean - k))
        s_low = max(0, s_low - (values[i] - mean + k))
        if s_high > h:
            shift_points.append(i)
            directions.append("up")
            s_high = 0.0
            s_low = 0.0
            mean = np.mean(values[max(0, i - 100) : i + 1])
        elif s_low > h:
            shift_points.append(i)
            directions.append("down")
            s_high = 0.0
            s_low = 0.0
            mean = np.mean(values[max(0, i - 100) : i + 1])

    return TrendShiftReport(shift_count=len(shift_points), shift_points=shift_points, directions=directions)


def check_nominal_ranges(values: np.ndarray, channel: str) -> RangeViolationReport:
    channel_min = float(np.min(values))
    channel_max = float(np.max(values))
    violations: list[dict] = []

    nom = NOMINAL_RANGES.get(channel)
    if nom is not None:
        lower = nom["p01"]
        upper = nom["p99"]
        for i, v in enumerate(values):
            if v < lower or v > upper:
                violations.append(
                    {
                        "index": i,
                        "value": float(v),
                        "limit": "lower" if v < lower else "upper",
                        "type": "nominal_range",
                    }
                )
    else:
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_val = q1 - 1.5 * iqr
        upper_val = q3 + 1.5 * iqr
        for i, v in enumerate(values):
            if v < lower_val or v > upper_val:
                violations.append(
                    {
                        "index": i,
                        "value": float(v),
                        "limit": "lower" if v < lower_val else "upper",
                        "type": "iqr_outlier",
                    }
                )

    return RangeViolationReport(channel_min=channel_min, channel_max=channel_max, violations=violations)


def detect_pyod(
    values: np.ndarray,
    timestamps: list[str],
    detector: str = "IForest",
    window_size: int = 50,
    contamination: float = 0.1,
    score_aggregation: str = "max",
    step: int = 1,
) -> PyodReport | None:
    if len(values) < window_size + 1:
        return None

    try:
        from pyod.models.ts_od import TimeSeriesOD

        clf = TimeSeriesOD(
            detector=detector,
            window_size=window_size,
            contamination=contamination,
            score_aggregation=score_aggregation,
            step=step,
        )
        clf.fit(values)
        scores = clf.decision_scores_
        labels = clf.labels_
        threshold = clf.threshold_
    except Exception:
        return None

    anomaly_indices = [int(i) for i, label in enumerate(labels) if label == 1]
    return PyodReport(
        channel="",
        start_time="",
        end_time="",
        detector=detector,
        window_size=window_size,
        n_timestamps=len(values),
        n_anomalies=len(anomaly_indices),
        anomaly_indices=anomaly_indices,
        anomaly_timestamps=[timestamps[i] for i in anomaly_indices],
        anomaly_scores=[float(scores[i]) for i in anomaly_indices],
        mean_score=float(np.mean(scores)),
        max_score=float(np.max(scores)),
        threshold=float(threshold),
    )


def preanalyze_segment(values: np.ndarray, points: list) -> DataProfile:
    from scipy import stats
    from scipy.signal import detrend
    from statsmodels.tsa.stattools import adfuller

    n = len(values)
    try:
        _, adf_pvalue, *_ = adfuller(values)
        is_stationary = adf_pvalue < 0.05
    except ValueError:
        adf_pvalue = 1.0
        is_stationary = True

    missing_ratio = float(np.isnan(values).sum() / n) if n > 0 else 0.0
    timestamps_arr = np.array([p.timestamp.timestamp() for p in points])
    intervals = np.diff(timestamps_arr)
    sampling_regularity = float(np.std(intervals) / np.mean(intervals)) if len(intervals) > 0 else 0.0

    detrended = detrend(values)
    noise_std = float(np.std(detrended))

    _, normality_p = stats.normaltest(values)
    is_normal = normality_p > 0.05

    slope, intercept, r_value, p_value, std_err = stats.linregress(np.arange(n), values)
    trend_pvalue = float(p_value)
    if trend_pvalue > 0.05:
        trend_direction = "flat"
    else:
        trend_direction = "up" if slope > 0 else "down"

    return DataProfile(
        stationarity_pvalue=float(adf_pvalue),
        is_stationary=is_stationary,
        missing_ratio=missing_ratio,
        sampling_regularity=sampling_regularity,
        noise_std=noise_std,
        is_normal=is_normal,
        trend_direction=trend_direction,
        trend_pvalue=trend_pvalue,
        segment_length=n,
        value_range=(float(values.min()), float(values.max())),
    )


@tool
def analyze(
    channel: str,
    start_time: datetime,
    end_time: datetime,
    methods: list[Method] = ["profile", "spikes", "shifts", "ranges", "pyod"],
    spike_threshold: Annotated[float, Field(ge=1.0, le=10.0)] = 3.5,
    shift_decision_threshold: Annotated[float, Field(ge=1.0, le=20.0)] = 5.0,
    shift_drift: Annotated[float, Field(ge=0.0, le=2.0)] = 0.25,
    pyod_detector: PyodDetector = "IForest",
    pyod_contamination: Annotated[float, Field(gt=0.0, le=0.5)] = 0.1,
    pyod_window_size: Annotated[int, Field(ge=5, le=500)] = 50,
    pyod_score_aggregation: ScoreAggregation = "max",
    pyod_step: Annotated[int, Field(ge=1, le=100)] = 1,
) -> AnalysisReport:
    """Run one or more anomaly detection methods on a telemetry window.

    Supports profile (stationarity/normality/trend), spikes (MAD-based z-score),
    shifts (CUSUM), ranges (channel-specific nominal P01-P99), and pyod
    (PyOD TimeSeriesOD with configurable detector).

    Args:
        channel: Telemetry channel name (e.g. "CADC0872").
        start_time: ISO-format start timestamp.
        end_time: ISO-format end timestamp.
        methods: Detection methods to run — any subset of "profile", "spikes", "shifts", "ranges", "pyod".
        spike_threshold: Z-score threshold for spike detection (1.0–10.0, default 3.5).
        shift_decision_threshold: CUSUM decision threshold in sigma units (1.0–20.0, default 5.0).
        shift_drift: CUSUM allowable drift in sigma units (0.0–2.0, default 0.25).
        pyod_detector: PyOD detector name — IForest, HBOS, KNN, LOF, PCA, OCSVM.
        pyod_contamination: Expected outlier proportion (0.0–0.5, default 0.1).
        pyod_window_size: Sliding window size for PyOD (5–500, default 50).
        pyod_score_aggregation: Window score aggregation — "max" or "mean".
        pyod_step: Step between consecutive windows (1–100, default 1).

    Returns:
        AnalysisReport with results for each requested method.
    """
    points = load_telemetry_range(channel, start_time.isoformat(), end_time.isoformat())
    if not points:
        return AnalysisReport(
            channel=channel,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            methods_run=methods,
            warnings=[f"No data found for channel={channel} in that time range"],
        )

    values = np.array([p.value for p in points])
    timestamps_str = [p.timestamp.isoformat() for p in points]
    warnings: list[str] = []

    result_profile: DataProfile | None = None
    result_spikes: SpikeReport | None = None
    result_shifts: TrendShiftReport | None = None
    result_ranges: RangeViolationReport | None = None
    result_pyod: PyodReport | None = None

    for method in methods:
        if method == "profile":
            result_profile = preanalyze_segment(values, points)
        elif method == "spikes":
            result_spikes = detect_spikes_mad(values, spike_threshold)
        elif method == "shifts":
            result_shifts = detect_shifts_cusum(values, shift_decision_threshold, shift_drift)
        elif method == "ranges":
            result_ranges = check_nominal_ranges(values, channel)
        elif method == "pyod":
            result_pyod = detect_pyod(
                values,
                timestamps_str,
                pyod_detector,
                pyod_window_size,
                pyod_contamination,
                pyod_score_aggregation,
                pyod_step,
            )
            if result_pyod is None:
                warnings.append(f"pyod: too few points ({len(values)}) for window_size={pyod_window_size}")

    return AnalysisReport(
        channel=channel,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        methods_run=methods,
        profile=result_profile,
        spikes=result_spikes,
        shifts=result_shifts,
        ranges=result_ranges,
        pyod=result_pyod,
        warnings=warnings,
    )
