from datetime import datetime

import numpy as np

from agent.models.reports import (
    AnalysisReport,
    AnomalousHoursReport,
    ComparisonReport,
    DailyReport,
    TelemetrySegment,
)
from agent.models.telemetry import Segment, TelemetryPoint
from agent.tools.analyze import (
    analyze,
    check_nominal_ranges,
    detect_shifts_cusum,
    detect_spikes_mad,
)
from agent.tools.compare_channels import compare_channels
from agent.tools.daily_report import generate_daily_report, get_anomalous_hours
from agent.tools.data_loader import _range_cache, _segment_cache
from agent.tools.fetch_telemetry import fetch_telemetry
from agent.tools.visualizer import visualize

TEST_TS = datetime(2025, 1, 1, 0, 0, 0)
TEST_TS_STR = "2025-01-01T00:00:00"
END_TS_STR = "2025-01-01T01:00:00"


def make_segment(values: list[float]) -> Segment:
    base_ts = datetime(2025, 1, 1, 0, 0, 0)
    points = [TelemetryPoint(timestamp=base_ts, value=v) for v in values]
    return Segment(segment_id=TEST_TS_STR, channel="TEST", points=points)


def _cache_segment(segment: Segment):
    _segment_cache[(segment.channel, segment.segment_id)] = segment
    _range_cache.clear()


# ── Internal detection functions ──


class TestSpikeDetector:
    def test_no_spikes_in_flat_data(self):
        values = np.array([5.0] * 100)
        result = detect_spikes_mad(values)
        assert result.spike_count == 0

    def test_detects_large_spike(self):
        values = np.array([1.0 + 0.001 * i for i in range(100)])
        values[50] = 100.0
        result = detect_spikes_mad(values)
        assert result.spike_count >= 1


class TestShiftDetector:
    def test_no_shifts_in_flat_data(self):
        values = np.array([5.0] * 50)
        result = detect_shifts_cusum(values)
        assert result.shift_count == 0

    def test_detects_step_change(self):
        values = np.array([1.0] * 25 + [100.0] * 25)
        result = detect_shifts_cusum(values)
        assert result.shift_count >= 1


class TestNominalRanges:
    def test_no_violations_in_normal_data(self):
        values = np.array([10.0 + (i % 5 - 2) for i in range(50)])
        result = check_nominal_ranges(values, "TEST")
        assert len(result.violations) == 0

    def test_detects_outliers(self):
        values = np.array([1.0] * 10 + [1000.0] + [1.0] * 10)
        result = check_nominal_ranges(values, "TEST")
        assert len(result.violations) >= 1


# ── Tools ──


class TestProfile:
    def test_flat_segment_is_stationary(self):
        values = [10.0 + (i % 2) * 1e-3 for i in range(30)]
        _cache_segment(make_segment(values))
        result = analyze.invoke(
            {
                "channel": "TEST",
                "start_time": TEST_TS,
                "end_time": datetime(2025, 1, 1, 0, 1, 0),
                "methods": ["profile"],
            }
        )
        assert result.profile is not None
        assert result.profile.is_stationary is True

    def test_trending_segment_has_trend_direction(self):
        values = [float(i) for i in range(50)]
        _cache_segment(make_segment(values))
        result = analyze.invoke(
            {
                "channel": "TEST",
                "start_time": TEST_TS,
                "end_time": datetime(2025, 1, 1, 0, 1, 0),
                "methods": ["profile"],
            }
        )
        assert result.profile is not None
        assert result.profile.trend_direction == "up"


class TestAnalyze:
    def test_returns_all_methods(self):
        values = [float(i % 10) for i in range(200)]
        _cache_segment(make_segment(values))
        result = analyze.invoke(
            {
                "channel": "TEST",
                "start_time": TEST_TS,
                "end_time": datetime(2025, 1, 1, 0, 0, 0),
                "methods": ["profile", "spikes", "shifts", "ranges"],
            }
        )
        assert isinstance(result, AnalysisReport)
        assert result.profile is not None
        assert result.spikes is not None
        assert result.shifts is not None
        assert result.ranges is not None

    def test_returns_selected_method_only(self):
        values = [5.0] * 50
        _cache_segment(make_segment(values))
        result = analyze.invoke(
            {
                "channel": "TEST",
                "start_time": TEST_TS,
                "end_time": datetime(2025, 1, 1, 0, 0, 0),
                "methods": ["spikes"],
            }
        )
        assert isinstance(result, AnalysisReport)
        assert result.spikes is not None
        assert result.shifts is None


class TestFetchTelemetry:
    def test_returns_known_data(self):
        values = [1.0, 2.0, 3.0]
        _cache_segment(make_segment(values))
        result = fetch_telemetry.invoke(
            {
                "channel": "TEST",
                "start_time": TEST_TS,
                "end_time": datetime(2025, 1, 1, 0, 0, 0),
            }
        )
        assert isinstance(result, TelemetrySegment)
        assert result.n_points == len(values)

    def test_empty_for_unknown_data(self):
        result = fetch_telemetry.invoke(
            {
                "channel": "UNKNOWN",
                "start_time": datetime(2025, 1, 1, 0, 0, 0),
                "end_time": datetime(2025, 1, 1, 0, 1, 0),
            }
        )
        assert result.n_points == 0


class TestCompareChannels:
    def test_returns_report_per_channel(self):
        values_a = [float(i) for i in range(30)]
        values_b = [float(i) for i in range(30)]
        _cache_segment(make_segment(values_a))
        seg2 = Segment(
            segment_id=TEST_TS_STR,
            channel="TEST2",
            points=[TelemetryPoint(timestamp=TEST_TS, value=v) for v in values_b],
        )
        _cache_segment(seg2)
        result = compare_channels.invoke(
            {
                "channels": ["TEST", "TEST2"],
                "start_time": TEST_TS,
                "end_time": datetime(2025, 1, 1, 0, 1, 0),
                "methods": ["spikes"],
            }
        )
        assert isinstance(result, ComparisonReport)
        assert len(result.windows) == 2


class TestVisualizer:
    def test_returns_base64_string(self):
        values = [float(i) for i in range(10)]
        _cache_segment(make_segment(values))
        result = visualize.invoke({"channel": "TEST", "start_time": TEST_TS_STR, "end_time": END_TS_STR})
        assert isinstance(result, str)
        assert len(result) > 100


class TestDailyReport:
    def test_returns_structure_for_known_date(self):
        result = generate_daily_report.invoke({"date": "2022-01-04"})
        assert isinstance(result, DailyReport)
        assert result.date == "2022-01-04"
        assert result.channels_checked >= 1
        assert result.total_windows >= 1
        assert isinstance(result.overall_severity, str)

    def test_empty_for_no_data_date(self):
        result = generate_daily_report.invoke({"date": "2099-12-31"})
        assert result.channels_checked == 0
        assert result.total_windows == 0
        assert result.overall_severity == "green"


class TestAnomalousHours:
    def test_returns_all_findings_for_date(self):
        result = get_anomalous_hours.invoke({"date": "2022-01-04"})
        assert isinstance(result, AnomalousHoursReport)
        assert result.date == "2022-01-04"
        assert result.total_hours_checked >= 1
        assert result.channel is None

    def test_filters_by_channel(self):
        result = get_anomalous_hours.invoke({"date": "2022-01-04", "channel": "CADC0872"})
        assert result.channel == "CADC0872"
        for f in result.findings:
            assert f.channel == "CADC0872"

    def test_empty_for_no_data(self):
        result = get_anomalous_hours.invoke({"date": "2099-12-31"})
        assert result.anomalous_hours == 0
        assert result.findings == []
