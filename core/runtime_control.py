import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
RUNTIME_STATE_PATH = os.path.join(DATABASE_DIR, "runtime_state.json")
CONTROL_STATE_PATH = os.path.join(DATABASE_DIR, "control_state.json")


def _safe_read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _safe_write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, default=str, indent=2)


def write_runtime_state(state):
    payload = dict(state or {})
    payload["updated_at_utc"] = datetime.utcnow().isoformat()
    _safe_write_json(RUNTIME_STATE_PATH, payload)


def read_runtime_state():
    return _safe_read_json(RUNTIME_STATE_PATH, {})


def read_control_state():
    return _safe_read_json(
        CONTROL_STATE_PATH,
        {"overrides": {}, "actions": []},
    )


def write_control_state(data):
    payload = data or {"overrides": {}, "actions": []}
    if "overrides" not in payload:
        payload["overrides"] = {}
    if "actions" not in payload:
        payload["actions"] = []
    _safe_write_json(CONTROL_STATE_PATH, payload)


def upsert_overrides(new_overrides):
    state = read_control_state()
    overrides = state.get("overrides", {})
    overrides.update(new_overrides or {})
    state["overrides"] = overrides
    write_control_state(state)
    return state


def enqueue_action(action_type, payload=None):
    state = read_control_state()
    actions = state.get("actions", [])
    actions.append(
        {
            "type": action_type,
            "payload": payload or {},
            "queued_at_utc": datetime.utcnow().isoformat(),
        }
    )
    state["actions"] = actions
    write_control_state(state)
    return state


def pop_actions():
    state = read_control_state()
    actions = state.get("actions", [])
    state["actions"] = []
    write_control_state(state)
    return actions
