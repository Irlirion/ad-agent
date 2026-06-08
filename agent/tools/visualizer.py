import base64
import io
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from langchain_core.tools import tool

from agent.tools.data_loader import load_telemetry_range


@tool(return_direct=True)
def visualize(channel: str, start_time: datetime, end_time: datetime) -> str:
    """Plot telemetry for a given channel and time range. Returns base64 PNG."""
    points = load_telemetry_range(channel, start_time.isoformat(), end_time.isoformat())
    if not points:
        return f"No data found for channel={channel} in that time range. Use list_segments() to see available windows."

    timestamps = [p.timestamp for p in points]
    values = [p.value for p in points]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(timestamps, values, color="steelblue", linewidth=1, label="Telemetry")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title(f"Time Range: {start_time.isoformat()} to {end_time.isoformat()} (Channel: {channel})")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")
