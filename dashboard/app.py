"""
Smart Home Dashboard — browser-based control panel.

Provides:
  • Live status of Ollama, Tool Broker, Tailscale, Voice/Secretary
  • Start/stop controls for all services
  • Interactive chat panel (sends queries through /v1/process)
  • Activity log showing every LLM input/output and tool call
  • Tailscale mesh network / RPI status
  • Voice assistant & Secretary engine status

Launch:  python -m dashboard.app          (from Smart_Home/)
   or:   python Smart_Home/dashboard/app.py
"""

import json
import os
import time
from collections import deque
from datetime import datetime

import dash
from dash import html, dcc, Input, Output, State, callback_context, no_update
import httpx
from dotenv import load_dotenv

from .process_manager import ProcessManager, ServiceStatus

# Lazy import for batch scheduler (avoid import errors if secretary not available)
try:
    from secretary.scheduler import batch_scheduler
except ImportError:
    batch_scheduler = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

BROKER_URL = os.getenv("TOOL_BROKER_URL", os.getenv("BROKER_URL", "http://localhost:8000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8050"))

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

manager = ProcessManager(
    ollama_url=OLLAMA_URL,
    broker_url=BROKER_URL,
    ollama_model=OLLAMA_MODEL,
)

# Activity log — deque so it auto-trims
activity_log: deque = deque(maxlen=500)
chat_history: list = []  # [{role, content, tool_calls, timestamp}]
seen_request_ids: set = set()  # Track audit entries we've already processed
dashboard_request_ids: set = set()  # Request IDs from dashboard chat (skip in poll)
chat_seen_ids: set = set()  # Audit entries already injected into chat


def _log(kind: str, data: dict):
    """Append an entry to the activity log."""
    activity_log.appendleft({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "kind": kind,
        **data,
    })


# ---------------------------------------------------------------------------
# Status badge helper
# ---------------------------------------------------------------------------

def _status_badge(status: ServiceStatus) -> html.Span:
    color_map = {
        ServiceStatus.RUNNING: "#22c55e",
        ServiceStatus.STARTING: "#eab308",
        ServiceStatus.STOPPED: "#6b7280",
        ServiceStatus.ERROR: "#ef4444",
    }
    return html.Span(
        status.value.upper(),
        style={
            "background": color_map.get(status, "#6b7280"),
            "color": "white",
            "padding": "2px 10px",
            "borderRadius": "12px",
            "fontSize": "12px",
            "fontWeight": "600",
            "letterSpacing": "0.5px",
        },
    )


def _mini_badge(online: bool) -> html.Span:
    """Small green/gray dot for peer status."""
    return html.Span("●", style={
        "color": "#22c55e" if online else "#6b7280",
        "marginRight": "6px",
        "fontSize": "10px",
    })


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

CARD = {
    "background": "#1e1e2e",
    "borderRadius": "12px",
    "padding": "20px",
    "marginBottom": "16px",
    "border": "1px solid #313244",
}
PAGE = {
    "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    "background": "#11111b",
    "color": "#cdd6f4",
    "minHeight": "100vh",
    "padding": "24px",
}
INPUT_STYLE = {
    "width": "100%",
    "padding": "12px 16px",
    "border": "1px solid #45475a",
    "borderRadius": "8px",
    "background": "#181825",
    "color": "#cdd6f4",
    "fontSize": "14px",
    "outline": "none",
}
BTN = {
    "padding": "10px 20px",
    "border": "none",
    "borderRadius": "8px",
    "cursor": "pointer",
    "fontSize": "14px",
    "fontWeight": "600",
}
BTN_PRIMARY = {**BTN, "background": "#89b4fa", "color": "#1e1e2e"}
BTN_SUCCESS = {**BTN, "background": "#a6e3a1", "color": "#1e1e2e"}
BTN_DANGER = {**BTN, "background": "#f38ba8", "color": "#1e1e2e"}
BTN_SECONDARY = {**BTN, "background": "#45475a", "color": "#cdd6f4"}
BTN_SMALL = {**BTN, "fontSize": "12px", "padding": "6px 14px"}
LABEL = {"fontSize": "11px", "color": "#6c7086", "textTransform": "uppercase", "letterSpacing": "1px", "marginBottom": "8px"}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def build_layout():
    return html.Div(style=PAGE, children=[
        # Header
        html.Div(style={"display": "flex", "alignItems": "center", "marginBottom": "24px", "gap": "16px"}, children=[
            html.H1("Smart Home Dashboard", style={"margin": 0, "fontSize": "28px", "color": "#cdd6f4"}),
            html.Span("v3.0", style={"color": "#6c7086", "fontSize": "14px"}),
        ]),

        # Three-column layout
        html.Div(style={
            "display": "grid",
            "gridTemplateColumns": "300px 1fr 320px",
            "gap": "20px",
            "alignItems": "start",
        }, children=[

            # ── LEFT COLUMN: Status + Controls ──
            html.Div(children=[
                # Core services status
                html.Div(style=CARD, children=[
                    html.H3("Core Services", style={"margin": "0 0 16px 0", "fontSize": "16px"}),
                    html.Div(id="status-panel", children=[
                        html.P("Checking…", style={"color": "#6c7086"}),
                    ]),
                    dcc.Interval(id="status-interval", interval=5_000, n_intervals=0),
                ]),

                # Service Controls
                html.Div(style=CARD, children=[
                    html.H3("Service Controls", style={"margin": "0 0 16px 0", "fontSize": "16px"}),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "8px"}, children=[
                        html.Button("Start Ollama", id="btn-start-ollama", style={**BTN_SUCCESS, **BTN_SMALL}),
                        html.Button("Stop Ollama", id="btn-stop-ollama", style={**BTN_DANGER, **BTN_SMALL}),
                        html.Button("Start Broker", id="btn-start-broker", style={**BTN_SUCCESS, **BTN_SMALL}),
                        html.Button("Stop Broker", id="btn-stop-broker", style={**BTN_DANGER, **BTN_SMALL}),
                    ]),
                    html.Hr(style={"borderColor": "#313244", "margin": "12px 0"}),
                    html.Button("Refresh All", id="btn-refresh", style={**BTN_SECONDARY, **BTN_SMALL, "width": "100%"}),
                    html.Div(id="control-feedback", style={"marginTop": "10px", "fontSize": "13px", "color": "#a6adc8"}),
                ]),

                # Config
                html.Div(style=CARD, children=[
                    html.P("Configuration", style=LABEL),
                    html.Table(style={"width": "100%", "fontSize": "13px"}, children=[
                        html.Tr([html.Td("Model", style={"color": "#6c7086"}), html.Td(OLLAMA_MODEL)]),
                        html.Tr([html.Td("Broker", style={"color": "#6c7086"}), html.Td(BROKER_URL)]),
                        html.Tr([html.Td("Ollama", style={"color": "#6c7086"}), html.Td(OLLAMA_URL)]),
                    ]),
                ]),
            ]),

            # ── CENTER COLUMN: Chat + Activity ──
            html.Div(children=[
                # Chat panel
                html.Div(style=CARD, children=[
                    html.H3("Chat", style={"margin": "0 0 12px 0", "fontSize": "16px"}),
                    html.Div(
                        id="chat-messages",
                        style={
                            "height": "400px",
                            "overflowY": "auto",
                            "padding": "12px",
                            "background": "#181825",
                            "borderRadius": "8px",
                            "marginBottom": "12px",
                            "display": "flex",
                            "flexDirection": "column",
                            "gap": "10px",
                        },
                        children=[html.P("Type a message to talk to Jarvis.", style={"color": "#6c7086", "fontStyle": "italic"})],
                    ),
                    html.Div(style={"display": "flex", "gap": "10px"}, children=[
                        dcc.Input(
                            id="chat-input",
                            placeholder="Ask me anything…",
                            style={**INPUT_STYLE, "flex": "1"},
                            debounce=False,
                            n_submit=0,
                        ),
                        html.Button("Send", id="btn-send", style=BTN_PRIMARY),
                    ]),
                ]),

                # Activity log
                html.Div(style=CARD, children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"}, children=[
                        html.H3("Activity Log", style={"margin": 0, "fontSize": "16px"}),
                        html.Button("Clear", id="btn-clear-log", style={**BTN, "background": "#313244", "color": "#a6adc8", "fontSize": "12px", "padding": "4px 12px"}),
                    ]),
                    html.Div(
                        id="activity-log",
                        style={
                            "height": "240px",
                            "overflowY": "auto",
                            "fontFamily": "'JetBrains Mono', 'Fira Code', monospace",
                            "fontSize": "12px",
                            "lineHeight": "1.6",
                            "padding": "12px",
                            "background": "#181825",
                            "borderRadius": "8px",
                        },
                    ),
                    dcc.Interval(id="log-interval", interval=2_000, n_intervals=0),
                ]),
            ]),

            # ── RIGHT COLUMN: Network + Voice ──
            html.Div(children=[
                # Tailscale / Network
                html.Div(style=CARD, children=[
                    html.H3("Network / Tailscale", style={"margin": "0 0 12px 0", "fontSize": "16px"}),
                    html.Div(id="tailscale-panel", children=[
                        html.P("Checking…", style={"color": "#6c7086"}),
                    ]),
                    dcc.Interval(id="tailscale-interval", interval=15_000, n_intervals=0),
                ]),

                # Voice / Secretary
                html.Div(style=CARD, children=[
                    html.H3("Voice / Secretary", style={"margin": "0 0 12px 0", "fontSize": "16px"}),
                    html.Div(id="voice-panel", children=[
                        html.P("Checking…", style={"color": "#6c7086"}),
                    ]),
                    html.Hr(style={"borderColor": "#313244", "margin": "10px 0"}),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "8px"}, children=[
                        html.Button("Start Voice", id="btn-start-voice", style={**BTN_SUCCESS, **BTN_SMALL}),
                        html.Button("Stop Voice", id="btn-stop-voice", style={**BTN_DANGER, **BTN_SMALL}),
                    ]),
                    html.Div(id="voice-control-feedback", style={"marginTop": "8px", "fontSize": "12px", "color": "#a6adc8"}),
                    dcc.Interval(id="voice-interval", interval=10_000, n_intervals=0),
                ]),

                # Broker Logs
                html.Div(style=CARD, children=[
                    html.H3("Broker Logs", style={"margin": "0 0 12px 0", "fontSize": "16px"}),
                    html.Div(
                        id="broker-logs",
                        style={
                            "height": "180px",
                            "overflowY": "auto",
                            "fontFamily": "'JetBrains Mono', monospace",
                            "fontSize": "11px",
                            "lineHeight": "1.5",
                            "padding": "10px",
                            "background": "#181825",
                            "borderRadius": "8px",
                            "color": "#a6adc8",
                        },
                    ),
                    dcc.Interval(id="broker-log-interval", interval=3_000, n_intervals=0),
                ]),

                # Batch Intelligence
                html.Div(style=CARD, children=[
                    html.H3("Batch Intelligence", style={"margin": "0 0 12px 0", "fontSize": "16px"}),
                    html.Div(id="batch-panel", children=[
                        html.P("Not started", style={"color": "#6c7086"}),
                    ]),
                    html.Hr(style={"borderColor": "#313244", "margin": "10px 0"}),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "8px"}, children=[
                        html.Button("Start Scheduler", id="btn-start-batch", style={**BTN_SUCCESS, **BTN_SMALL}),
                        html.Button("Run Now", id="btn-run-batch", style={**BTN_PRIMARY, **BTN_SMALL}),
                    ]),
                    html.Div(id="batch-control-feedback", style={"marginTop": "8px", "fontSize": "12px", "color": "#a6adc8"}),
                    dcc.Interval(id="batch-interval", interval=30_000, n_intervals=0),
                ]),
            ]),
        ]),

        # Hidden stores
        dcc.Store(id="chat-store", data=[]),
        dcc.Interval(id="chat-poll-interval", interval=3_000, n_intervals=0),
    ])


# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    title="Smart Home Dashboard",
    update_title=None,
    suppress_callback_exceptions=True,
)
app.layout = build_layout


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("status-panel", "children"),
    Input("status-interval", "n_intervals"),
    Input("btn-refresh", "n_clicks"),
    prevent_initial_call=False,
)
def update_status(n, _clicks):
    """Poll health endpoints and render status."""
    manager.check_all()

    def _row(svc):
        sub_text = svc.model or svc.detail or ""
        return html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"},
            children=[
                html.Div([
                    html.Strong(svc.name, style={"fontSize": "14px"}),
                    html.Br(),
                    html.Span(sub_text, style={"fontSize": "12px", "color": "#6c7086"}),
                ]),
                _status_badge(svc.status),
            ],
        )

    return [_row(manager.ollama), _row(manager.broker)]


@app.callback(
    Output("control-feedback", "children"),
    Input("btn-start-broker", "n_clicks"),
    Input("btn-stop-broker", "n_clicks"),
    Input("btn-start-ollama", "n_clicks"),
    Input("btn-stop-ollama", "n_clicks"),
    prevent_initial_call=True,
)
def handle_controls(start_broker, stop_broker, start_ollama, stop_ollama):
    """Start/stop services."""
    trigger = callback_context.triggered_id
    if trigger == "btn-start-broker":
        msg = manager.start_broker()
        _log("CONTROL", {"message": msg})
        return msg
    elif trigger == "btn-stop-broker":
        msg = manager.stop_broker()
        _log("CONTROL", {"message": msg})
        return msg
    elif trigger == "btn-start-ollama":
        msg = manager.start_ollama()
        _log("CONTROL", {"message": msg})
        return msg
    elif trigger == "btn-stop-ollama":
        msg = manager.stop_ollama()
        _log("CONTROL", {"message": msg})
        return msg
    return no_update


@app.callback(
    Output("chat-messages", "children"),
    Output("chat-store", "data"),
    Output("chat-input", "value"),
    Input("btn-send", "n_clicks"),
    Input("chat-input", "n_submit"),
    State("chat-input", "value"),
    State("chat-store", "data"),
    prevent_initial_call=True,
)
def send_message(n_clicks, n_submit, text, _history):
    """Send user message to /v1/process, auto-execute tool calls, render response."""
    if not text or not text.strip():
        return no_update, no_update, no_update

    text = text.strip()
    now = datetime.now().strftime("%H:%M:%S")

    # Add user message to server-side chat history (single source of truth)
    chat_history.append({"role": "user", "content": text, "ts": now})
    _log("USER_INPUT", {"text": text})

    # Call Tool Broker
    try:
        resp = httpx.post(
            f"{BROKER_URL}/v1/process",
            json={"text": text},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()

        # Track this request so the poll callback skips it
        req_id = resp.headers.get("x-request-id")
        if req_id:
            dashboard_request_ids.add(req_id)

        assistant_text = data.get("text", "")
        tool_calls = data.get("tool_calls", [])
        requires_confirmation = data.get("requires_confirmation", False)
        tier = data.get("tier", "unknown")

        _log("LLM_RESPONSE", {
            "text": assistant_text[:200],
            "tool_calls": len(tool_calls),
            "requires_confirmation": requires_confirmation,
            "tier": tier,
        })

        for tc in tool_calls:
            _log("TOOL_CALL", {
                "tool": tc.get("tool_name"),
                "args": json.dumps(tc.get("arguments", {})),
                "confidence": tc.get("confidence"),
                "confirm": tc.get("requires_confirmation", False),
            })

        # Auto-execute tool calls that don't require confirmation
        tool_results = []
        for tc in tool_calls:
            if tc.get("requires_confirmation") or requires_confirmation:
                tool_results.append({
                    "tool_name": tc.get("tool_name"),
                    "status": "awaiting_confirmation",
                    "message": "Requires user confirmation",
                })
                continue
            try:
                exec_resp = httpx.post(
                    f"{BROKER_URL}/v1/execute",
                    json={
                        "type": "tool_call",
                        "tool_name": tc.get("tool_name"),
                        "arguments": tc.get("arguments", {}),
                    },
                    timeout=30.0,
                )
                exec_resp.raise_for_status()
                exec_data = exec_resp.json()
                tool_results.append({
                    "tool_name": tc.get("tool_name"),
                    "status": exec_data.get("status", "ok"),
                    "result": exec_data.get("result", exec_data.get("message", "")),
                })
                _log("TOOL_RESULT", {
                    "tool": tc.get("tool_name"),
                    "status": exec_data.get("status", "ok"),
                })
            except Exception as exec_err:
                tool_results.append({
                    "tool_name": tc.get("tool_name"),
                    "status": "error",
                    "result": str(exec_err),
                })
                _log("TOOL_ERROR", {"tool": tc.get("tool_name"), "error": str(exec_err)})

        chat_history.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "requires_confirmation": requires_confirmation,
            "tier": tier,
            "ts": datetime.now().strftime("%H:%M:%S"),
        })

    except httpx.ConnectError:
        err_msg = "Cannot connect to Tool Broker. Is it running?"
        chat_history.append({"role": "error", "content": err_msg, "ts": now})
        _log("ERROR", {"message": err_msg})
    except Exception as exc:
        err_msg = f"Error: {exc}"
        chat_history.append({"role": "error", "content": err_msg, "ts": now})
        _log("ERROR", {"message": err_msg})

    # Render from server-side chat history
    elements = _render_chat(chat_history)
    return elements, list(chat_history), ""


def _render_chat(history):
    """Convert chat history into Dash HTML elements."""
    if not history:
        return [html.P("Type a message to talk to Jarvis.", style={"color": "#6c7086", "fontStyle": "italic"})]

    elements = []
    for msg in history:
        role = msg.get("role", "")
        ts = msg.get("ts", "")

        if role == "user":
            source = msg.get("source")
            header_items = [html.Span(ts, style={"fontSize": "10px", "color": "#6c7086"})]
            if source:
                header_items.append(html.Span(f"via {source}", style={
                    "fontSize": "9px", "color": "#fab387", "fontFamily": "monospace",
                    "background": "#181825", "padding": "1px 6px", "borderRadius": "4px",
                }))
            elements.append(html.Div(style={
                "alignSelf": "flex-end",
                "background": "#313244",
                "padding": "10px 14px",
                "borderRadius": "12px 12px 2px 12px",
                "maxWidth": "80%",
            }, children=[
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "6px"}, children=header_items),
                html.P(msg["content"], style={"margin": "4px 0 0 0"}),
            ]))

        elif role == "assistant":
            tier = msg.get("tier", "")
            source = msg.get("source")
            tier_color = "#a6e3a1" if tier == "local" else "#89b4fa" if tier == "sidecar" else "#6c7086"
            tier_label = f"[{tier}]" if tier else ""

            header_badges = [html.Span(ts, style={"fontSize": "10px", "color": "#6c7086"})]
            if tier_label:
                header_badges.append(html.Span(tier_label, style={
                    "fontSize": "9px", "color": tier_color, "fontFamily": "monospace",
                    "background": "#181825", "padding": "1px 6px", "borderRadius": "4px",
                }))
            if source:
                header_badges.append(html.Span(f"via {source}", style={
                    "fontSize": "9px", "color": "#fab387", "fontFamily": "monospace",
                    "background": "#181825", "padding": "1px 6px", "borderRadius": "4px",
                }))

            children = [
                html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=header_badges),
                html.P(msg["content"], style={"margin": "4px 0 0 0"}),
            ]

            # Show tool calls with execution results
            tool_results = msg.get("tool_results", [])
            for i, tc in enumerate(msg.get("tool_calls", [])):
                conf = tc.get("confidence", 0)
                confirm = tc.get("requires_confirmation", False)

                # Find matching result
                result = tool_results[i] if i < len(tool_results) else None
                result_status = (result or {}).get("status", "")
                result_text = (result or {}).get("result", "")

                # Status indicator
                if result_status == "success":
                    status_icon = "OK"
                    status_color = "#a6e3a1"
                elif result_status == "awaiting_confirmation":
                    status_icon = "CONFIRM?"
                    status_color = "#f9e2af"
                elif result_status == "error":
                    status_icon = "FAIL"
                    status_color = "#f38ba8"
                else:
                    status_icon = ""
                    status_color = "#6c7086"

                tc_children = [
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                        html.Strong(f"Tool: {tc.get('tool_name', '?')}"),
                        html.Span(f"conf={conf:.0%}", style={"color": "#6c7086", "fontSize": "11px"}),
                        html.Span(status_icon, style={
                            "color": status_color, "fontSize": "10px", "fontWeight": "bold",
                            "background": "#181825", "padding": "1px 6px", "borderRadius": "3px",
                        }) if status_icon else html.Span(),
                    ]),
                    html.Pre(json.dumps(tc.get("arguments", {}), indent=2), style={
                        "margin": "4px 0 0 0", "color": "#a6adc8",
                        "fontSize": "11px", "whiteSpace": "pre-wrap",
                    }),
                ]

                # Show execution result if available
                if result_text:
                    result_display = result_text if isinstance(result_text, str) else json.dumps(result_text, indent=2)
                    if len(result_display) > 300:
                        result_display = result_display[:300] + "..."
                    tc_children.append(html.Div(style={
                        "marginTop": "4px", "padding": "4px 8px",
                        "background": "#11111b", "borderRadius": "4px",
                        "fontSize": "11px", "color": status_color,
                    }, children=[
                        html.Span("Result: ", style={"fontWeight": "bold"}),
                        html.Span(result_display),
                    ]))

                children.append(html.Div(style={
                    "marginTop": "8px", "padding": "8px 12px",
                    "background": "#1e1e2e", "borderRadius": "6px",
                    "borderLeft": f"3px solid {status_color if status_icon else ('#f38ba8' if confirm else '#89b4fa')}",
                    "fontSize": "12px", "fontFamily": "'JetBrains Mono', monospace",
                }, children=tc_children))

            elements.append(html.Div(style={
                "alignSelf": "flex-start",
                "background": "#1e1e2e",
                "padding": "10px 14px",
                "borderRadius": "12px 12px 12px 2px",
                "maxWidth": "85%",
                "border": "1px solid #313244",
            }, children=children))

        elif role == "error":
            elements.append(html.Div(style={
                "background": "#1e1e2e",
                "border": "1px solid #f38ba8",
                "padding": "10px 14px",
                "borderRadius": "8px",
                "color": "#f38ba8",
                "fontSize": "13px",
            }, children=[html.P(msg["content"], style={"margin": 0})]))

    return elements


# ---------------------------------------------------------------------------
# External chat injection — polls audit log for non-dashboard interactions
# ---------------------------------------------------------------------------

@app.callback(
    Output("chat-messages", "children", allow_duplicate=True),
    Output("chat-store", "data", allow_duplicate=True),
    Input("chat-poll-interval", "n_intervals"),
    prevent_initial_call=True,
)
def poll_external_chat(n):
    """Inject external LLM interactions (curl, Jarvis, API) into the chat panel."""
    changed = False

    try:
        resp = httpx.get(
            f"{BROKER_URL}/v1/audit/recent",
            params={"limit": 50},
            timeout=3.0,
        )
        if resp.status_code != 200:
            return no_update, no_update

        entries = resp.json().get("entries", [])
        for entry in reversed(entries):  # oldest first
            req_id = entry.get("request_id")
            if not req_id:
                continue
            if req_id in chat_seen_ids:
                continue
            # Dashboard-originated — already in chat via send_message
            if req_id in dashboard_request_ids:
                chat_seen_ids.add(req_id)
                continue
            # Only care about /v1/process interactions
            if entry.get("endpoint") != "/v1/process":
                chat_seen_ids.add(req_id)
                continue

            chat_seen_ids.add(req_id)

            # Parse user input from JSON body
            input_summary = entry.get("input_summary", "")
            user_text = input_summary
            try:
                input_json = json.loads(input_summary)
                user_text = input_json.get("text", input_summary)
            except (json.JSONDecodeError, TypeError):
                pass

            # Parse output
            output_summary = entry.get("output_summary", "")
            extra = entry.get("extra") or {}
            tier = extra.get("tier", "unknown")

            ts = entry.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts).strftime("%H:%M:%S")
            except Exception:
                pass

            source = entry.get("client_ip", "api")

            if user_text:
                chat_history.append({
                    "role": "user",
                    "content": user_text,
                    "ts": ts,
                    "source": source,
                })

            if output_summary:
                chat_history.append({
                    "role": "assistant",
                    "content": output_summary,
                    "tool_calls": [],
                    "tool_results": [],
                    "tier": tier,
                    "ts": ts,
                    "source": source,
                })

            changed = True
    except Exception:
        pass

    if not changed:
        return no_update, no_update

    return _render_chat(chat_history), list(chat_history)


@app.callback(
    Output("activity-log", "children"),
    Input("log-interval", "n_intervals"),
    Input("btn-clear-log", "n_clicks"),
    prevent_initial_call=False,
)
def update_activity_log(n, clear_clicks):
    """Poll Tool Broker audit log and render activity log pane."""
    trigger = callback_context.triggered_id
    if trigger == "btn-clear-log":
        activity_log.clear()
        seen_request_ids.clear()
        return [html.Span("Log cleared.", style={"color": "#6c7086"})]

    # Poll the Tool Broker audit log for new entries
    try:
        resp = httpx.get(f"{BROKER_URL}/v1/audit/recent", params={"limit": 50}, timeout=3.0)
        if resp.status_code == 200:
            audit_entries = resp.json().get("entries", [])
            # Process newest entries first, but add them in reverse so oldest appears at bottom
            new_entries = [e for e in reversed(audit_entries) if e.get("request_id") not in seen_request_ids]
            
            for entry in new_entries:
                request_id = entry.get("request_id")
                if not request_id:
                    continue
                seen_request_ids.add(request_id)
                
                endpoint = entry.get("endpoint", "")
                method = entry.get("method", "")
                ts_str = entry.get("timestamp", "")
                ts = datetime.fromisoformat(ts_str).strftime("%H:%M:%S") if ts_str else ""
                
                # Only log meaningful interactions
                if endpoint == "/v1/process":
                    input_summary = entry.get("input_summary", "")
                    output_summary = entry.get("output_summary", "")
                    tool_calls_count = entry.get("tool_calls", 0)
                    latency = entry.get("latency_ms", 0)
                    
                    if input_summary:
                        _log("USER_INPUT", {"text": input_summary, "source": "broker"})
                    if output_summary:
                        _log("LLM_RESPONSE", {
                            "text": output_summary[:150],
                            "tool_calls": tool_calls_count,
                            "latency_ms": latency,
                        })
                
                elif endpoint == "/v1/execute":
                    input_summary = entry.get("input_summary", "")
                    output_summary = entry.get("output_summary", "")
                    if input_summary:
                        _log("TOOL_CALL", {"exec": input_summary[:100]})
                    if output_summary:
                        _log("TOOL_CALL", {"result": output_summary[:100]})
                
                # Log errors
                if entry.get("error"):
                    _log("ERROR", {"endpoint": endpoint, "error": entry.get("error")})
    
    except Exception:
        pass  # Silently fail if broker is unreachable

    if not activity_log:
        return [html.Span("No activity yet.", style={"color": "#6c7086", "fontStyle": "italic"})]

    lines = []
    kind_colors = {
        "USER_INPUT": "#89b4fa",
        "LLM_RESPONSE": "#a6e3a1",
        "TOOL_CALL": "#cba6f7",
        "CONTROL": "#fab387",
        "ERROR": "#f38ba8",
    }
    for entry in list(activity_log)[:100]:
        kind = entry.get("kind", "")
        ts = entry.get("timestamp", "")
        color = kind_colors.get(kind, "#cdd6f4")

        # Build display text
        parts = {k: v for k, v in entry.items() if k not in ("kind", "timestamp")}
        detail = "  ".join(f"{k}={v}" for k, v in parts.items())

        lines.append(html.Div(style={"marginBottom": "2px"}, children=[
            html.Span(f"[{ts}] ", style={"color": "#6c7086"}),
            html.Span(f"{kind:<14}", style={"color": color, "fontWeight": "600"}),
            html.Span(f" {detail}", style={"color": "#a6adc8"}),
        ]))
    return lines


# ---------------------------------------------------------------------------
# Tailscale / Network callback
# ---------------------------------------------------------------------------

@app.callback(
    Output("tailscale-panel", "children"),
    Input("tailscale-interval", "n_intervals"),
    Input("btn-refresh", "n_clicks"),
    prevent_initial_call=False,
)
def update_tailscale(n, _clicks):
    """Poll Tailscale status and render network panel."""
    ts = manager.check_tailscale()

    if not ts["installed"]:
        return [
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                html.Span("●", style={"color": "#6b7280"}),
                html.Span("Tailscale not installed", style={"fontSize": "13px"}),
            ]),
            html.P("Install: brew install tailscale", style={"fontSize": "12px", "color": "#6c7086", "margin": "8px 0 0 0"}),
        ]

    if not ts["running"]:
        return [
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "8px"}, children=[
                html.Span("●", style={"color": "#f38ba8"}),
                html.Span("Tailscale installed but not connected", style={"fontSize": "13px"}),
            ]),
            html.P("Run: tailscale up", style={"fontSize": "12px", "color": "#6c7086", "margin": "8px 0 0 0"}),
        ]

    children = []

    # Self
    children.append(html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "10px"}, children=[
        html.Span("This Mac", style={"fontSize": "13px", "fontWeight": "600"}),
        html.Span(ts["ip"] or "—", style={"fontSize": "12px", "color": "#89b4fa", "fontFamily": "monospace"}),
    ]))

    # RPI highlight
    rpi = ts.get("rpi")
    if rpi:
        color = "#22c55e" if rpi["online"] else "#f38ba8"
        children.append(html.Div(style={
            "background": "#181825",
            "borderRadius": "8px",
            "padding": "10px 12px",
            "marginBottom": "10px",
            "borderLeft": f"3px solid {color}",
        }, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                html.Strong(f"🍓 {rpi['name']}", style={"fontSize": "13px"}),
                html.Span("ONLINE" if rpi["online"] else "OFFLINE", style={
                    "fontSize": "11px",
                    "fontWeight": "600",
                    "color": color,
                }),
            ]),
            html.Span(f"{rpi['ip'] or '—'}  ·  {rpi.get('os', '')}", style={"fontSize": "11px", "color": "#6c7086"}),
        ]))
    else:
        children.append(html.P("No Raspberry Pi detected in mesh", style={"fontSize": "12px", "color": "#6c7086", "fontStyle": "italic", "margin": "0 0 10px 0"}))

    # Other peers
    other_peers = [p for p in ts["peers"] if p != rpi]
    if other_peers:
        children.append(html.P("Peers", style={"fontSize": "11px", "color": "#6c7086", "textTransform": "uppercase", "letterSpacing": "1px", "margin": "8px 0 4px 0"}))
        for peer in other_peers[:8]:
            children.append(html.Div(style={"display": "flex", "justifyContent": "space-between", "padding": "2px 0"}, children=[
                html.Span([_mini_badge(peer["online"]), peer["name"]], style={"fontSize": "12px"}),
                html.Span(peer["ip"] or "—", style={"fontSize": "11px", "color": "#6c7086", "fontFamily": "monospace"}),
            ]))

    # Summary
    children.append(html.P(ts["detail"], style={"fontSize": "11px", "color": "#6c7086", "marginTop": "8px"}))
    return children


# ---------------------------------------------------------------------------
# Voice / Secretary callback
# ---------------------------------------------------------------------------

@app.callback(
    Output("voice-panel", "children"),
    Input("voice-interval", "n_intervals"),
    Input("btn-refresh", "n_clicks"),
    prevent_initial_call=False,
)
def update_voice(n, _clicks):
    """Poll voice service processes."""
    vs = manager.check_voice_services()

    def _svc_row(label, active, description=""):
        color = "#22c55e" if active else "#6b7280"
        return html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "6px 0"}, children=[
            html.Div([
                html.Strong(label, style={"fontSize": "13px"}),
                html.Br() if description else "",
                html.Span(description, style={"fontSize": "11px", "color": "#6c7086"}) if description else "",
            ]),
            html.Span("●", style={"color": color, "fontSize": "14px"}),
        ])

    children = [
        _svc_row("Jarvis Voice Loop", vs["voice_loop"], "Wake word → STT → LLM → TTS"),
        _svc_row("Secretary Engine", vs["secretary"], "Live transcription + notes"),
        _svc_row("Whisper STT", vs["whisper"], "Speech-to-text model"),
    ]

    # Show rich voice status if available from status file
    voice_status = vs.get("voice_status")
    if voice_status:
        state = voice_status.get("state", "unknown")
        interactions = voice_status.get("interactions", 0)
        errors = voice_status.get("errors", 0)
        children.append(html.Hr(style={"borderColor": "#313244", "margin": "8px 0"}))
        children.append(html.Div(style={
            "background": "#181825", "borderRadius": "6px", "padding": "8px 12px",
            "borderLeft": "3px solid #89b4fa",
        }, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                html.Span(f"State: {state}", style={"fontSize": "12px", "fontWeight": "600"}),
                html.Span(f"{interactions} queries · {errors} errors", style={"fontSize": "11px", "color": "#6c7086"}),
            ]),
        ]))
    else:
        children.append(html.Hr(style={"borderColor": "#313244", "margin": "8px 0"}))
        children.append(html.P(vs["detail"], style={"fontSize": "12px", "color": "#6c7086", "margin": 0}))

    if not any([vs["voice_loop"], vs["secretary"], vs["whisper"]]):
        children.append(html.Div(style={"marginTop": "10px", "padding": "8px 12px", "background": "#181825", "borderRadius": "6px"}, children=[
            html.P("Voice services not running.", style={"fontSize": "12px", "color": "#6c7086", "margin": "0 0 4px 0"}),
            html.P("Use the Start Voice button above, or:", style={"fontSize": "11px", "color": "#6c7086", "margin": 0}),
            html.Pre("python -m jarvis", style={"fontSize": "11px", "color": "#a6adc8", "margin": "4px 0 0 0"}),
        ]))

    return children


# ---------------------------------------------------------------------------
# Voice controls callback
# ---------------------------------------------------------------------------

@app.callback(
    Output("voice-control-feedback", "children"),
    Input("btn-start-voice", "n_clicks"),
    Input("btn-stop-voice", "n_clicks"),
    prevent_initial_call=True,
)
def handle_voice_controls(start_clicks, stop_clicks):
    """Start/stop the Jarvis voice loop."""
    trigger = callback_context.triggered_id
    if trigger == "btn-start-voice":
        msg = manager.start_voice()
        _log("CONTROL", {"message": msg})
        return msg
    elif trigger == "btn-stop-voice":
        msg = manager.stop_voice()
        _log("CONTROL", {"message": msg})
        return msg
    return no_update


# ---------------------------------------------------------------------------
# Broker Logs callback
# ---------------------------------------------------------------------------

@app.callback(
    Output("broker-logs", "children"),
    Input("broker-log-interval", "n_intervals"),
    prevent_initial_call=False,
)
def update_broker_logs(n):
    """Show recent broker subprocess logs."""
    lines = manager.get_broker_logs()
    if not lines:
        return [html.Span("No broker logs (broker may have been started externally).", style={"color": "#6c7086", "fontStyle": "italic"})]
    return [html.Div(line, style={"whiteSpace": "pre-wrap"}) for line in lines[-50:]]


# ---------------------------------------------------------------------------
# Batch Intelligence callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("batch-panel", "children"),
    Input("batch-interval", "n_intervals"),
    Input("btn-refresh", "n_clicks"),
    prevent_initial_call=False,
)
def update_batch_panel(n, _clicks):
    """Show batch scheduler status and last results."""
    if batch_scheduler is None:
        return [html.P("Scheduler module not available", style={"color": "#f38ba8", "fontSize": "12px"})]

    children = []

    # Running status
    running = batch_scheduler.is_running
    color = "#22c55e" if running else "#6b7280"
    children.append(html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"}, children=[
        html.Strong("Scheduler", style={"fontSize": "13px"}),
        html.Span("● ACTIVE" if running else "● IDLE", style={
            "color": color, "fontSize": "12px", "fontWeight": "600",
        }),
    ]))

    # Last results
    results = batch_scheduler.last_results
    if not results:
        children.append(html.P("No analysis results yet. Click 'Run Now' to start.", style={"fontSize": "12px", "color": "#6c7086"}))
    else:
        for r in results:
            status = r.get("status", "unknown")
            s_color = "#22c55e" if status == "success" else "#f38ba8" if status == "error" else "#6c7086"
            children.append(html.Div(style={
                "padding": "6px 10px", "background": "#181825", "borderRadius": "6px",
                "marginBottom": "6px", "borderLeft": f"3px solid {s_color}",
            }, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                    html.Strong(r.get("job_name", "?"), style={"fontSize": "12px"}),
                    html.Span(status.upper(), style={"color": s_color, "fontSize": "11px", "fontWeight": "600"}),
                ]),
                html.P(r.get("summary", "")[:120], style={"fontSize": "11px", "color": "#a6adc8", "margin": "4px 0 0 0"}),
            ]))

    return children


@app.callback(
    Output("batch-control-feedback", "children"),
    Input("btn-start-batch", "n_clicks"),
    Input("btn-run-batch", "n_clicks"),
    prevent_initial_call=True,
)
def handle_batch_controls(start_clicks, run_clicks):
    """Start scheduler or run batch jobs immediately."""
    if batch_scheduler is None:
        return "Scheduler module not available"

    trigger = callback_context.triggered_id
    if trigger == "btn-start-batch":
        if batch_scheduler.is_running:
            batch_scheduler.stop()
            _log("CONTROL", {"message": "Batch scheduler stopped"})
            return "Scheduler stopped."
        else:
            batch_scheduler.start()
            _log("CONTROL", {"message": "Batch scheduler started"})
            return f"Scheduler started (interval: {batch_scheduler.interval}s)"
    elif trigger == "btn-run-batch":
        results = batch_scheduler.run_once()
        job_count = len(results)
        _log("CONTROL", {"message": f"Batch run: {job_count} jobs completed"})
        return f"Completed {job_count} batch jobs"
    return no_update


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    import webbrowser
    import threading

    url = f"http://localhost:{DASHBOARD_PORT}"
    print(f"\n  Smart Home Dashboard -> {url}\n")
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()

    app.run(
        host="127.0.0.1",
        port=DASHBOARD_PORT,
        debug=False,
    )


if __name__ == "__main__":
    main()
