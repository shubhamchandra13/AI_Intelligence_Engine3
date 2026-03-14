import os
import sqlite3
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from core.runtime_control import (
    read_control_state,
    read_runtime_state,
    upsert_overrides,
    enqueue_action,
)
from core.ai_agent import GeminiAIAgent

app = FastAPI(title="AI Intelligence Terminal API", version="1.0.0")
ai_agent = GeminiAIAgent()

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "database", "trades.db")

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
def chat_with_agent(payload: ChatRequest):
    response = ai_agent.chat(payload.query)
    return {"response": response}

class ControlOverrideRequest(BaseModel):
    min_confidence: Optional[float] = None
    force_market_open: Optional[bool] = None
    pause_entries: Optional[bool] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/state")
def get_state():
    return read_runtime_state()


@app.get("/why-no-trade")
def why_no_trade():
    state = read_runtime_state()
    return {
        "entry_allowed": state.get("entry_allowed"),
        "best_index": state.get("best_index"),
        "reasons": state.get("why_no_trade", []),
        "updated_at_utc": state.get("updated_at_utc"),
    }


@app.get("/decision")
def decision():
    state = read_runtime_state()
    return state.get("decision_output", {})


@app.get("/controls")
def get_controls():
    return read_control_state()


@app.post("/controls/overrides")
def set_overrides(payload: ControlOverrideRequest):
    overrides: Dict[str, Any] = {}
    if payload.min_confidence is not None:
        overrides["MIN_CONFIDENCE"] = payload.min_confidence
    if payload.force_market_open is not None:
        overrides["FORCE_MARKET_OPEN"] = payload.force_market_open
    if payload.pause_entries is not None:
        overrides["PAUSE_ENTRIES"] = payload.pause_entries
    return upsert_overrides(overrides)


@app.post("/controls/actions/retrain-ml")
def trigger_retrain_ml():
    return enqueue_action("RETRAIN_ML", {})


@app.post("/controls/actions/close-all")
def trigger_close_all():
    """Manual trigger to exit all positions immediately."""
    return enqueue_action("MANUAL_EXIT_ALL", {"reason": "User Manual Square-off"})


@app.post("/controls/actions/close-trade/{index_name}")
def trigger_close_trade(index_name: str):
    """Manual trigger to exit a specific trade for a specific index."""
    return enqueue_action("MANUAL_EXIT_TRADE", {"index": index_name, "reason": "User Manual Exit"})


@app.get("/trades/recent")
def recent_trades(limit: int = 25):
    limit = max(1, min(limit, 200))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, index_name, direction, entry_price, exit_price, pnl,
               confidence, regime, iv_regime, entry_time, exit_time, timestamp
        FROM trades
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "trades": rows}


@app.get("/features/recent")
def recent_features(limit: int = 25):
    limit = max(1, min(limit, 500))
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ai_feature_store)")
    available_columns = {row[1] for row in cur.fetchall()}
    if not available_columns:
        conn.close()
        return {"count": 0, "features": []}
    desired_columns = [
        "id", "trade_id", "index_name", "direction", "regime", "iv_regime",
        "confidence", "indicator_score", "indicator_confluence",
        "ai_quality_score", "ai_uncertainty_score", "ai_risk_multiplier",
        "stat_win_probability", "ml_win_probability", "meta_quality_probability",
        "ml_model_version", "structure_bias", "relative_score", "oi_bias", "oi_pcr",
        "oi_call_wall", "oi_put_wall", "theta_minutes_to_expiry", "theta_decay_score",
        "iv_score", "option_strike", "option_type", "option_ltp", "option_bid",
        "option_ask", "spread_pct", "estimated_slippage_pct", "liquidity_score",
        "portfolio_heat_pct", "allocation_weight", "timestamp",
    ]
    selected_columns = [col for col in desired_columns if col in available_columns]
    if not selected_columns:
        selected_columns = ["id", "timestamp"]
    cur.execute(
        f"""
        SELECT {", ".join(selected_columns)}
        FROM ai_feature_store
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"count": len(rows), "features": rows}


@app.get("/intelligence")
def intelligence():
    state = read_runtime_state()
    return state.get("intelligence_stats", {})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8051, log_level="info")
