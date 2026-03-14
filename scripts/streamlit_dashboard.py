import requests
import streamlit as st


API_BASE = st.sidebar.text_input("API Base URL", value="http://127.0.0.1:8000")


def api_get(path, default=None):
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return default


def api_post(path, payload=None, default=None):
    try:
        resp = requests.post(f"{API_BASE}{path}", json=payload or {}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return default


st.set_page_config(page_title="AI System Dashboard", layout="wide")
st.title("AI System Engine Dashboard")

state = api_get("/state", {})
why = api_get("/why-no-trade", {})
controls = api_get("/controls", {"overrides": {}})
recent = api_get("/trades/recent?limit=20", {"trades": []})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Market Open", str(state.get("market_open")))
col2.metric("Best Index", str(state.get("best_index")))
col3.metric("Entry Allowed", str(state.get("entry_allowed")))
col4.metric("Live Price", str(state.get("live_price")))

st.subheader("Why No Trade")
reasons = why.get("reasons", [])
if reasons:
    for r in reasons:
        st.write(f"- {r}")
else:
    st.write("No diagnostics yet.")

st.subheader("Live Probabilities")
st.json(
    {
        "stat_probability": state.get("live_setup_probability"),
        "ml_probability": state.get("live_ml_probability"),
        "meta_label": state.get("live_meta_label"),
    }
)

st.subheader("Controls")
with st.form("controls_form"):
    min_conf = st.number_input(
        "MIN_CONFIDENCE",
        min_value=0.0,
        max_value=100.0,
        value=float((controls.get("overrides") or {}).get("MIN_CONFIDENCE", 30)),
        step=1.0,
    )
    force_open = st.checkbox(
        "FORCE_MARKET_OPEN",
        value=bool((controls.get("overrides") or {}).get("FORCE_MARKET_OPEN", False)),
    )
    pause_entries = st.checkbox(
        "PAUSE_ENTRIES",
        value=bool((controls.get("overrides") or {}).get("PAUSE_ENTRIES", False)),
    )
    submitted = st.form_submit_button("Apply Overrides")
    if submitted:
        result = api_post(
            "/controls/overrides",
            {
                "min_confidence": min_conf,
                "force_market_open": force_open,
                "pause_entries": pause_entries,
            },
            default={"status": "failed"},
        )
        st.success(f"Updated: {result}")

if st.button("Trigger ML Retrain"):
    result = api_post("/controls/actions/retrain-ml", {}, default={"status": "failed"})
    st.info(result)

st.subheader("Recent Trades")
st.dataframe(recent.get("trades", []), use_container_width=True)

st.caption(f"Last runtime update: {state.get('updated_at_utc')}")

