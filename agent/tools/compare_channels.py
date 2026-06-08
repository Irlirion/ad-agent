from datetime import datetime

import numpy as np
from langchain_core.tools import tool

from agent.models.reports import ComparisonReport, Method
from agent.tools.analyze import analyze
from agent.tools.data_loader import load_telemetry_range


@tool
def compare_channels(
    channels: list[str],
    start_time: datetime,
    end_time: datetime,
    methods: list[Method] = ["profile", "spikes", "shifts", "ranges", "pyod"],
) -> ComparisonReport:
    """Run anomaly detection on multiple channels over the same time window and compare results.

    Args:
        channels: List of channel names to compare (e.g. ["CADC0872", "CADC0873"]).
        start_time: ISO-format start timestamp.
        end_time: ISO-format end timestamp.
        methods: Detection methods to run on each channel.

    Returns:
        ComparisonReport with per-channel AnalysisReports and cross-channel correlation.
    """
    reports = []
    values_list = []

    for ch in channels:
        data = load_telemetry_range(ch, start_time.isoformat(), end_time.isoformat())
        if data:
            values_list.append(np.array([p.value for p in data]))
        report = analyze.invoke(
            {
                "channel": ch,
                "start_time": start_time,
                "end_time": end_time,
                "methods": methods,
            }
        )
        reports.append(report)

    correlation = None
    if len(values_list) >= 2:
        min_len = min(len(v) for v in values_list)
        if min_len >= 3:
            aligned = [v[:min_len] for v in values_list]
            corr_matrix = np.corrcoef(aligned)
            triu_inds = np.triu_indices(len(channels), k=1)
            if triu_inds[0].size > 0:
                correlation = float(np.mean(corr_matrix[triu_inds]))

    channels_agree = len(set(tuple(r.methods_run) for r in reports)) == 1

    return ComparisonReport(windows=reports, methods=methods, correlation=correlation, channels_agree=channels_agree)
