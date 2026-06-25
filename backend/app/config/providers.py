"""Provider registry: lists all available image generation providers.

Each provider has a uniquely name used as the `provider` parameter
in generate API calls. Providers auto-detect availability based on
installed dependencies and environment variables.

To add a new provider:
  1. Add a dict entry below with name/label/description/env_vars
  2. Implement the provider class in imagegen.py
"""

import os
import shutil
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ProviderMeta:
    name: str          # unique key e.g. "mock", "fal-fast", "codex"
    label: str         # display name e.g. "Fal.ai Flux Schnell"
    description: str   # one-liner
    env_vars: list[str] = field(default_factory=list)  # required env vars
    is_available: bool = False
    is_default: bool = False


PROVIDER_REGISTRY: list[ProviderMeta] = [
    ProviderMeta(
        name="mock",
        label="Mock 本地合成",
        description="纯本地 Pillow 合成，无 AI，快速预览布局效果",
        env_vars=[],
        is_default=True,
    ),
    ProviderMeta(
        name="fal-fast",
        label="Fal.ai Flux Schnell (快)",
        description="fal.ai flux/schnell 模型，~2s/张，适合批量生成",
        env_vars=["FAL_KEY"],
    ),
    ProviderMeta(
        name="fal-pro",
        label="Fal.ai Flux Pro (精)",
        description="fal.ai flux/pro 模型，~8s/张，高质量电商图",
        env_vars=["FAL_KEY"],
    ),
    ProviderMeta(
        name="codex",
        label="Codex Imagegen",
        description="OpenAI Codex 内置 imagegen，高质量，需 Codex CLI",
        env_vars=[],
    ),
    ProviderMeta(
        name="siliconflow-fast",
        label="硅基流动 Flux Schnell (快)",
        description="国内硅基流动 Flux Schnell，~2s/张，不超时",
        env_vars=["SILICONFLOW_KEY"],
    ),
    ProviderMeta(
        name="siliconflow-pro",
        label="硅基流动 Flux Pro (精)",
        description="国内硅基流动 Flux Pro，~8s/张，高质感",
        env_vars=["SILICONFLOW_KEY"],
    ),
    ProviderMeta(
        name="agnes",
        label="Agnes AI (免费)",
        description="新加坡 Sapiens AI 全模态免费 API，图生图/文生图，速度快",
        env_vars=["AGNES_API_KEY"],
    ),
    ProviderMeta(
        name="volcengine-ark",
        label="火山方舟 Seedream 5.0",
        description="火山方舟豆包 Seedream 5.0，真图生图，产品一致性最佳",
        env_vars=["VOLCENGINE_ARK_API_KEY"],
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
        # codex needs the CLI binary
        if meta.name == "codex":
            if not shutil.which("codex"):
                ok = False
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
            "available": avail.get(meta.name, False),
            "is_default": meta.is_default,
        })
    return result


def get_default_provider() -> str:
    """Pick the best available provider, falling back to mock."""
    avail = detect_availability()
    for meta in PROVIDER_REGISTRY:
        if meta.is_default:
            continue
        if avail.get(meta.name):
            return meta.name
    return "mock"
