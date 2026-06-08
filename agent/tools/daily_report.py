import csv
from datetime import UTC, datetime, timedelta

from langchain_core.tools import tool

from agent.models.reports import AnomalousHoursReport, AnomalyFinding, ChannelSummary, DailyReport
from agent.settings import settings
from agent.tools.analyze import check_nominal_ranges, detect_shifts_cusum, detect_spikes_mad, preanalyze_segment
from agent.tools.data_loader import _window_start

SEGMENTS_PATH = settings.segments_path


def _parse_date(date_str: str) -> str:
    date_str = date_str.strip()
    if date_str == "yesterday":
        return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    return date_str


def _compute_anomaly_score(
    spike_count: int,
    shift_count: int,
    violations: int,
    is_stationary: bool,
) -> float:
    score = 0.0
    score += spike_count * 3.0
    score += shift_count * 30.0
    score += violations * 15.0
    score += 0.0 if is_stationary else 50.0
    return score


def _analyze_channel(channel: str, windows: set[str]) -> tuple[list[AnomalyFinding], int, float]:
    windows_sorted = sorted(windows)
    anomalous = 0
    max_score = 0.0
    findings: list[AnomalyFinding] = []

    for ws in windows_sorted:
        ws_dt = datetime.fromisoformat(ws)
        if ws_dt.tzinfo is None:
            ws_dt = ws_dt.replace(tzinfo=UTC)
        end_ws = (ws_dt + timedelta(hours=1)).isoformat()

        from agent.tools.data_loader import load_telemetry_range

        raw_points = load_telemetry_range(channel, ws, end_ws)
        if not raw_points:
            continue
        import numpy as np

        values_arr = np.array([p.value for p in raw_points])
        profile = preanalyze_segment(values_arr, raw_points)
        spikes = detect_spikes_mad(values_arr)
        shifts = detect_shifts_cusum(values_arr)
        ranges = check_nominal_ranges(values_arr, channel)

        score = _compute_anomaly_score(
            spike_count=spikes.spike_count,
            shift_count=shifts.shift_count,
            violations=len(ranges.violations),
            is_stationary=profile.is_stationary,
        )

        if score > max_score:
            max_score = score

        if score > 0:
            anomalous += 1
            evidence = []
            if spikes.spike_count > 0:
                evidence.append(f"{spikes.spike_count} spike(s)")
            if shifts.shift_count > 0:
                evidence.append(f"{shifts.shift_count} shift(s)")
            if ranges.violations:
                evidence.append(f"{len(ranges.violations)} range violation(s)")
            if not profile.is_stationary:
                evidence.append(f"non-stationary ({profile.trend_direction} trend)")

            findings.append(
                AnomalyFinding(
                    channel=channel,
                    timestamp=ws,
                    composite_score=score,
                    spike_count=spikes.spike_count,
                    shift_count=shifts.shift_count,
                    range_violations=len(ranges.violations),
                    is_stationary=profile.is_stationary,
                    trend_direction=profile.trend_direction,
                    evidence=evidence,
                )
            )

    return findings, anomalous, max_score


def _collect_windows(target: str) -> dict[str, set[str]]:
    pairs: dict[str, set[str]] = {}
    with open(SEGMENTS_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ch = row["channel"]
            ws = _window_start(row["timestamp"])
            if ws.startswith(target):
                pairs.setdefault(ch, set()).add(ws)
    return pairs


@tool
def generate_daily_report(date: str) -> DailyReport:
    """Scan all channels for a given day and produce a ranked anomaly report.

    Args:
        date: Date in YYYY-MM-DD format (or "yesterday" for previous day).
    """
    target = _parse_date(date)
    pairs = _collect_windows(target)

    if not any(pairs.values()):
        return DailyReport(
            date=target,
            channels_checked=0,
            total_windows=0,
            anomalous_windows=0,
            overall_severity="green",
            channel_summaries=[],
            top_anomalies=[],
        )

    all_findings: list[AnomalyFinding] = []
    channel_summaries: list[ChannelSummary] = []

    for channel in sorted(pairs):
        findings, anomalous, max_score = _analyze_channel(channel, pairs[channel])
        all_findings.extend(findings)

        if anomalous == 0:
            status = "normal"
        elif max_score < 10:
            status = "watch"
        else:
            status = "anomalous"

        channel_summaries.append(
            ChannelSummary(
                channel=channel,
                windows_checked=len(pairs[channel]),
                anomalous_windows=anomalous,
                max_anomaly_score=max_score,
                status=status,
            )
        )

    all_findings.sort(key=lambda f: f.composite_score, reverse=True)
    top_anomalies = all_findings[:10]
    anomalous_count = sum(1 for cs in channel_summaries if cs.status != "normal")
    total_windows = sum(cs.windows_checked for cs in channel_summaries)

    if any(cs.status == "anomalous" for cs in channel_summaries):
        severity = "red"
    elif any(cs.status == "watch" for cs in channel_summaries):
        severity = "yellow"
    else:
        severity = "green"

    return DailyReport(
        date=target,
        channels_checked=len(channel_summaries),
        total_windows=total_windows,
        anomalous_windows=anomalous_count,
        overall_severity=severity,
        channel_summaries=channel_summaries,
        top_anomalies=top_anomalies,
    )


@tool
def get_anomalous_hours(date: str, channel: str | None = None) -> AnomalousHoursReport:
    """List all anomalous 1-hour windows for a given day, optionally filtered by channel.

    Args:
        date: Date in YYYY-MM-DD format (or "yesterday" for previous day).
        channel: Optional channel name to filter by (e.g. "CADC0872").
    """
    target = _parse_date(date)
    pairs = _collect_windows(target)

    if channel:
        channels_to_check = {channel: pairs.get(channel, set())}
    else:
        channels_to_check = pairs

    total_windows = sum(len(wins) for wins in channels_to_check.values())

    if not any(channels_to_check.values()):
        return AnomalousHoursReport(
            date=target,
            channel=channel,
            total_hours_checked=total_windows,
            anomalous_hours=0,
            findings=[],
        )

    all_findings: list[AnomalyFinding] = []
    for ch in sorted(channels_to_check):
        findings, _, _ = _analyze_channel(ch, channels_to_check[ch])
        all_findings.extend(findings)

    all_findings.sort(key=lambda f: f.composite_score, reverse=True)

    return AnomalousHoursReport(
        date=target,
        channel=channel,
        total_hours_checked=total_windows,
        anomalous_hours=len(all_findings),
        findings=all_findings,
    )
