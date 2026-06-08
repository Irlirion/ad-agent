from datetime import datetime

from langchain_core.tools import tool

from agent.models.reports import TelemetrySegment
from agent.tools.data_loader import load_telemetry_range


@tool
def fetch_telemetry(channel: str, start_time: datetime, end_time: datetime) -> TelemetrySegment:
    """Fetch raw telemetry values for a time window. Returns timestamps and values for direct inspection.

    Args:
        channel: Telemetry channel name (e.g. "CADC0872").
        start_time: ISO-format start timestamp.
        end_time: ISO-format end timestamp.

    Returns:
        TelemetrySegment with raw values.
    """
    points = load_telemetry_range(channel, start_time.isoformat(), end_time.isoformat())
    if not points:
        return TelemetrySegment(
            channel=channel,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            timestamps=[],
            values=[],
            n_points=0,
            warning=f"No data found for channel={channel} in that time range",
        )

    return TelemetrySegment(
        channel=channel,
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        timestamps=[p.timestamp.isoformat() for p in points],
        values=[p.value for p in points],
        n_points=len(points),
    )
