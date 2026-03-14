from datetime import datetime
import os
import requests
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware

from core.runtime_control import read_runtime_state


APP_TITLE = "AI Intelligence Terminal Dashboard"
BASE_DIR = os.path.dirname(__file__)
API_BASE_URL = "http://localhost:8051" # Default API Port

ASSETS = {
    "style.css": os.path.join(BASE_DIR, "dashboard_style.css"),
    "app.js": os.path.join(BASE_DIR, "dashboard_app.js"),
}
INDEX_PATH = os.path.join(BASE_DIR, "dashboard_index.html")

app = FastAPI(title=APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.post("/chat")
def proxy_chat(body: Dict[str, Any]):
    """Proxy chat requests to the main API server."""
    try:
        response = requests.post(f"{API_BASE_URL}/chat", json=body, timeout=40)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runtime-state")
def runtime_state():
    state = read_runtime_state()
    if not state:
        raise HTTPException(status_code=404, detail="Runtime state not initialized yet.")
    payload = dict(state)
    payload["served_at_utc"] = datetime.utcnow().isoformat()
    return payload


@app.get("/api/health")
def health():
    state = read_runtime_state()
    return {
        "status": "ok",
        "runtime_exists": bool(state),
        "updated_at": state.get("updated_at_utc"),
    }


@app.get("/static/{asset_name}")
def serve_static(asset_name: str):
    path = ASSETS.get(asset_name)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Static asset not found.")
    media_type = "text/css" if asset_name.endswith(".css") else "application/javascript"
    return FileResponse(path, media_type=media_type)


@app.get("/", include_in_schema=False)
def index():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    raise HTTPException(status_code=404, detail="Dashboard UI not found.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("dashboard_server:app", host="0.0.0.0", port=8050, log_level="info")
