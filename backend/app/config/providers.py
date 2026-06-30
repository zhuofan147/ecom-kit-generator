"""Provider registry: lists all available image generation providers.

Each provider has a uniquely name used as the `provider` parameter
in generate API calls. Providers auto-detect availability based on
installed dependencies and environment variables.

To add a new provider:
  1. Add a dict entry below with name/label/description/env_vars
  2. Implement the provider class in imagegen.py
"""

import os
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ProviderMeta:
    name: str          # unique key e.g. "fal-fast", "agnes"
    label: str         # display name e.g. "Fal.ai Flux Schnell"
    description: str   # one-liner
    env_vars: list[str] = field(default_factory=list)  # required env vars
    endpoint: str = ""     # API endpoint URL
    model_id: str = ""     # model identifier for the provider
    provider_class: str = ""  # class in imagegen.py, e.g. "AgnesProvider"
    is_available: bool = False
    is_default: bool = False


_PROVIDER_ENDPOINTS = {
    "agnes": "https://apihub.agnes-ai.com/v1/images/generations",
    "volcengine": "https://ark.cn-beijing.volces.com/api/v3",
}

PROVIDER_REGISTRY: list[ProviderMeta] = [
    ProviderMeta(
        name="agnes",
        label="Agnes AI (免费)",
        description="新加坡 Sapiens AI 全模态免费 API，图生图/文生图，速度快",
        env_vars=["AGNES_API_KEY"],
        endpoint=_PROVIDER_ENDPOINTS["agnes"],
        model_id="agnes-image-2.0-flash",
        provider_class="AgnesProvider",
    ),
    ProviderMeta(
        name="volcengine-ark",
        label="火山方舟 Seedream 5.0",
        description="火山方舟豆包 Seedream 5.0，真图生图，产品一致性最佳",
        env_vars=["VOLCENGINE_ARK_API_KEY"],
        endpoint=_PROVIDER_ENDPOINTS["volcengine"],
        model_id="doubao-seedream-5-0-260128",
        provider_class="VolcEngineArkProvider",
    ),
    ProviderMeta(
        name="gpt-image-2",
        label="GPT Image-2 (Agnes兼容)",
        description="Agnes gpt-image-2 模型，图生图/文生图",
        env_vars=["AGNES_API_KEY"],
        endpoint=_PROVIDER_ENDPOINTS["agnes"],
        model_id="gpt-image-2",
        provider_class="AgnesProvider",
    ),
    ProviderMeta(
        name="codex",
        label="Codex CLI (本地)",
        description="OpenAI Codex CLI imagegen skill，无需 API key",
        env_vars=[],
        endpoint="",
        model_id="",
        provider_class="CodexImagegenProvider",
    ),
]


def detect_availability() -> dict[str, bool]:
    """Check which providers are available on this machine."""
    available: dict[str, bool] = {}
    for meta in PROVIDER_REGISTRY:
        ok = True
        for var in meta.env_vars:
            if not os.environ.get(var):
                ok = False
                break
        available[meta.name] = ok
    return available


def get_provider_list() -> list[dict]:
    """Return full provider list with availability for the frontend."""
    avail = detect_availability()
    result = []
    for meta in PROVIDER_REGISTRY:
        result.append({
            "name": meta.name,
            "label": meta.label,
            "description": meta.description,
            "model_id": meta.model_id,
            "endpoint": meta.endpoint,
            "available": avail.get(meta.name, False),
            "is_default": meta.is_default,
        })
    return result


def get_default_provider() -> str:
    """Pick the best available provider based on env vars."""
    avail = detect_availability()
    for meta in PROVIDER_REGISTRY:
        if avail.get(meta.name):
            return meta.name
    # No provider has API key configured — return empty, caller decides fallback
    return ""
