"""Providers API — list available AI image generation providers + LLM test/list-models."""

import json
import logging
import time
import urllib.request
import urllib.error
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import OUTPUT_DIR
from app.config.providers import get_provider_list, get_default_provider
from app.services.http_client import ssl_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["providers"])
SETTINGS_PATH = OUTPUT_DIR / "settings.json"


# ── LLM test / list-models request model ──────────────────────────

class LlmTestRequest(BaseModel):
    api_url: str = ""
    api_key: str = ""
    model: str = ""
    model_type: str = "all"


# ── existing provider endpoints ───────────────────────────────────

# In-memory store for frontend-synced enabled providers
_enabled_providers: set[str] = set()


@router.get("/providers")
async def list_providers():
    providers = get_provider_list()
    if _enabled_providers:
        # Filter: only show providers the frontend has enabled in Settings
        for p in providers:
            p["available"] = p["available"] and p["name"] in _enabled_providers
    return {
        "providers": providers,
        "default": get_default_provider(),
    }


class SyncEnabledRequest(BaseModel):
    enabled_names: list[str] = Field(default_factory=list)


@router.post("/providers/enabled")
async def sync_enabled_providers(request: SyncEnabledRequest):
    """Receive enabled provider names from frontend Settings."""
    global _enabled_providers
    _enabled_providers = set(request.enabled_names)
    logger.info(f"Synced enabled providers: {_enabled_providers}")
    return {"ok": True, "enabled": list(_enabled_providers)}


class SharedSettings(BaseModel):
    settingsVersion: int = 2
    theme: str = "light"
    llmConfigs: list[dict] = Field(default_factory=list)
    imageConfigs: list[dict] = Field(default_factory=list)
    visionConfigs: list[dict] = Field(default_factory=list)
    selectedLlmConfigId: str = ""
    selectedImageConfigId: str = ""
    selectedVisionConfigId: str = ""
    providers: list[str] = Field(default_factory=list)


@router.get("/settings")
async def get_settings():
    if not SETTINGS_PATH.exists():
        return {"settings": None}
    try:
        return {"settings": json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))}
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to read shared settings from %s", SETTINGS_PATH)
        return {"settings": None}


@router.post("/settings")
async def save_settings(settings: SharedSettings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"ok": True}


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
            "Content-Type": "application/json",
            **auth_headers(request.api_key),
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
    """Fetch available model IDs from LLM API, or image providers from registry."""
    # Image generation: try custom api_url first, fallback to registry
    if request.model_type == "image":
        if not request.api_key.strip():
            return {"models": [], "error": "请先填写 API Key"}
        if request.api_url:
            try:
                url = _models_url(request.api_url)
                req = Request(
                    url,
                    headers={"Authorization": f"Bearer {request.api_key}"} if request.api_key else {},
                )
                with urlopen(req, timeout=15, context=ssl_context()) as resp:
                    data = json.loads(resp.read())
                models = filter_model_ids(
                    [m.get("id", "") for m in data.get("data", []) if m.get("id")],
                    "image",
                )
                if models:
                    return {"models": models}
                return {"models": [], "error": "未识别到生图模型"}
            except HTTPError as e:
                body = e.read().decode(errors="replace")[:300]
                return {"models": [], "error": f"HTTP {e.code}: {body}"}
            except URLError as e:
                return {"models": [], "error": str(e.reason)}
            except Exception as e:
                logger.info("Image list-models from %s failed: %s", request.api_url, e)
                return {"models": [], "error": str(e)}
        providers = get_provider_list()
        models = [p["model_id"] for p in providers if p.get("model_id")]
        return {"models": models}

    url = _models_url(request.api_url)
    req = Request(
        url,
        headers=auth_headers(request.api_key),
    )
    try:
        with urlopen(req, timeout=15, context=ssl_context()) as resp:
            data = json.loads(resp.read())
        models = filter_model_ids([m.get("id", "") for m in data.get("data", []) if m.get("id")], request.model_type)
        return {"models": models}
    except HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        return {"models": [], "error": f"HTTP {e.code}: {body}"}
    except URLError as e:
        return {"models": [], "error": str(e.reason)}


# ── URL helpers ────────────────────────────────────────────────────

def _chat_completions_url(base_url: str) -> str:
    base = _api_base_url(base_url)
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def _models_url(base_url: str) -> str:
    base = _api_base_url(base_url)
    if base.endswith("/models"):
        return base
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"


def _api_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    for suffix in ("/images/generations", "/chat/completions"):
        if base.endswith(suffix):
            return base.removesuffix(suffix)
    return base


def auth_headers(api_key: str) -> dict[str, str]:
    key = api_key.strip()
    return {"Authorization": f"Bearer {key}"} if key else {}


VISION_MODEL_PATTERNS = (
    "vision",
    "visual",
    "vl",
    "glm-4v",
    "gpt-4o",
    "gpt-4.1",
    "gemini",
    "internvl",
    "minicpm-v",
    "llava",
    "qwen3.6-plus",
)

IMAGE_MODEL_PATTERNS = (
    "image",
    "img",
    "seedream",
    "flux",
    "stable-diffusion",
    "sdxl",
    "sd3",
    "dall-e",
    "gpt-image",
    "imagen",
    "ideogram",
    "recraft",
    "midjourney",
    "kandinsky",
    "kolors",
    "cogview",
    "jimeng",
    "wanx",
)


def filter_model_ids(models: list[str], model_type: str = "all") -> list[str]:
    if model_type == "vision":
        return [model for model in models if _looks_like_vision_model(model)]
    if model_type == "image":
        return [model for model in models if _looks_like_image_model(model)]
    return models


def _looks_like_vision_model(model: str) -> bool:
    lowered = model.lower()
    return any(pattern in lowered for pattern in VISION_MODEL_PATTERNS)


def _looks_like_image_model(model: str) -> bool:
    lowered = model.lower()
    return any(pattern in lowered for pattern in IMAGE_MODEL_PATTERNS)
