"""Providers API — list available AI image generation providers + LLM test/list-models."""

import json
import time
import urllib.request
import urllib.error
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config.providers import get_provider_list, get_default_provider
from app.services.http_client import ssl_context

router = APIRouter(prefix="/api", tags=["providers"])


# ── LLM test / list-models request model ──────────────────────────

class LlmTestRequest(BaseModel):
    api_url: str = ""
    api_key: str = ""
    model: str = ""


# ── existing provider endpoints ───────────────────────────────────

@router.get("/providers")
async def list_providers():
    return {
        "providers": get_provider_list(),
        "default": get_default_provider(),
    }


# ── test LLM connectivity ─────────────────────────────────────────

@router.post("/test-llm")
async def test_llm_connection(request: LlmTestRequest):
    """Test LLM API connectivity with a minimal chat completion request."""
    url = _chat_completions_url(request.api_url)
    payload = {
        "model": request.model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
    }
    req = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {request.api_key}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urlopen(req, timeout=15, context=ssl_context()) as resp:
            data = json.loads(resp.read())
        latency_ms = int((time.time() - t0) * 1000)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")[:100]
        return {"success": True, "latency_ms": latency_ms, "response": content}
    except HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        return {"success": False, "error": f"HTTP {e.code}: {body}"}
    except URLError as e:
        return {"success": False, "error": str(e.reason)}


# ── list available models ─────────────────────────────────────────

@router.post("/list-models")
async def list_models(request: LlmTestRequest):
    """Fetch available model IDs from LLM API."""
    url = _models_url(request.api_url)
    req = Request(
        url,
        headers={"Authorization": f"Bearer {request.api_key}"},
    )
    try:
        with urlopen(req, timeout=15, context=ssl_context()) as resp:
            data = json.loads(resp.read())
        models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
        return {"models": models}
    except HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        return {"models": [], "error": f"HTTP {e.code}: {body}"}
    except URLError as e:
        return {"models": [], "error": str(e.reason)}


# ── URL helpers ────────────────────────────────────────────────────

def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _models_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/models"):
        return base
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"
