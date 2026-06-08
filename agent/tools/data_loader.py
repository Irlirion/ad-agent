import csv
from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool

from agent.models.telemetry import Segment, TelemetryPoint
from agent.settings import settings

SEGMENTS_PATH = settings.segments_path
_segment_cache: dict[tuple[str, str], Segment] = {}
_range_cache: dict[tuple[str, str, str], list[TelemetryPoint]] = {}


def _window_start(ts_str: str) -> str:
    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    return ts.replace(minute=0, second=0, microsecond=0).isoformat()


@tool
def list_segments() -> str:
    """List available telemetry time windows. Returns channel names with their 1-hour window counts."""
    windows: dict[str, set[str]] = {}
    with open(SEGMENTS_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = row["channel"]
            window = _window_start(row["timestamp"])
            windows.setdefault(ch, set()).add(window)

    lines = []
    for ch in sorted(windows):
        times = sorted(windows[ch])
        n = len(times)
        lines.append(f"  Channel {ch}: {n} one-hour windows (from {times[0]} to {times[-1]})")

    total = sum(len(v) for v in windows.values())
    return f"Dataset: {total} one-hour windows across {len(windows)} channels:\n" + "\n".join(lines)


def _load_and_cache_segment(channel: str, timestamp: str) -> Segment | None:
    """Internal: load telemetry data, cache it, and return the Segment (or None if no data)."""
    start = _window_start(timestamp)
    key = (channel, start)
    if key in _segment_cache:
        return _segment_cache[key]

    start_dt = datetime.fromisoformat(start)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=UTC)
    end_dt = start_dt + timedelta(hours=1)

    points: list[TelemetryPoint] = []
    sampling_rate: float | None = None
    with open(SEGMENTS_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["channel"] != channel:
                continue
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if start_dt <= ts < end_dt:
                points.append(
                    TelemetryPoint(
                        timestamp=ts,
                        value=float(row["value"]),
                    )
                )
                if sampling_rate is None:
                    sampling_rate = float(row["sampling"])

    if not points:
        return None

    seg = Segment(
        segment_id=start,
        channel=channel,
        points=points,
        sampling_rate=sampling_rate,
    )
    _segment_cache[key] = seg
    return seg


def ensure_segment(channel: str, timestamp: str) -> Segment | None:
    """Load and cache segment if missing. Returns Segment or None if no data."""
    return _load_and_cache_segment(channel, timestamp)


def load_telemetry_range(channel: str, start_time: str, end_time: str) -> list[TelemetryPoint]:
    """Load telemetry data for a channel within [start_time, end_time).

    Checks both caches (range cache and legacy segment cache) before reading from CSV.
    """
    range_key = (channel, start_time, end_time)
    if range_key in _range_cache:
        return _range_cache[range_key]

    seg_key = (channel, start_time)
    if seg_key in _segment_cache:
        return _segment_cache[seg_key].points

    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=UTC)
    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=UTC)

    points: list[TelemetryPoint] = []
    with open(SEGMENTS_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["channel"] != channel:
                continue
            ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if start_dt <= ts < end_dt:
                points.append(
                    TelemetryPoint(
                        timestamp=ts,
                        value=float(row["value"]),
                    )
                )
    _range_cache[range_key] = points
    return points
