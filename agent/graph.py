from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from agent.settings import settings
from agent.tools.analyze import analyze
from agent.tools.compare_channels import compare_channels
from agent.tools.daily_report import generate_daily_report, get_anomalous_hours
from agent.tools.data_loader import list_segments
from agent.tools.fetch_telemetry import fetch_telemetry
from agent.tools.visualizer import visualize

tools = [
    list_segments,
    fetch_telemetry,
    analyze,
    compare_channels,
    visualize,
    generate_daily_report,
    get_anomalous_hours,
]

model = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)

SYSTEM_PROMPT = (
    "You are a satellite telemetry anomaly detection agent. "
    "You investigate telemetry data like a data scientist — forming hypotheses, testing them, and iterating.\n\n"
    "## Workflow\n"
    "1. **Discover**: Call list_segments() to see available channels and time windows.\n"
    "2. **Sample data**: Call fetch_telemetry(channel, start, end) to inspect raw values.\n"
    "3. **Characterize + Detect**: Call analyze(channel, start, end, methods=[...], **params). "
    "Available methods: profile (stationarity, normality, trend direction), "
    "spikes (MAD z-score), shifts (CUSUM change point), ranges (nominal P01-P99), "
    "pyod (PyOD TimeSeriesOD with IForest/HBOS/KNN/etc.). "
    "Tune parameters via spike_threshold, shift_decision_threshold, pyod_detector, pyod_contamination, etc.\n"
    "4. **Cross-reference**: Call compare_channels([chA, chB], start, end) to correlate multiple channels.\n"
    "5. **Present**: Call visualize(channel, start, end) to generate a presentation-quality plot for the operator.\n\n"
    "## Daily reports\n"
    f"When asked about daily status, call {generate_daily_report.name}(date) to scan all channels. "
    f"Call {get_anomalous_hours.name}(date, channel) to drill into a specific channel's anomalous hours. "
    "Always mention specific timestamps and findings from the report.\n\n"
    "## Time arithmetic\n"
    "- When computing time windows, always wrap past 23:59:59 to the next day "
    "(e.g., 23:00 + 2h = 01:00 next day, not 25:00).\n"
    "- All tools with start_time and end_time require BOTH parameters. Never omit end_time.\n\n"
    "## Guidelines\n"
    "- Start broad, then narrow down. Don't jump to a specific detector without context.\n"
    ""
    "- When you find anomalies, cross-reference with compare_channels() to check related channels.\n"
    "- Tell the operator what you found concisely — don't dump raw values.\n"
    "- If a method returns too few points, try a smaller window_size or different method."
)

graph = create_agent(
    model=model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)
