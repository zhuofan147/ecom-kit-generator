"""Image generation: abstract provider + placeholder compositor for all kit types."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from app.services.http_client import ssl_context
from app.services.template_engine import KitType


@dataclass(frozen=True)
class ImageGenerationRequest:
    product_image_path: Path
    output_path: Path
    prompt: str
    width: int
    height: int
    reference_image_paths: list[Path] = field(default_factory=list)
    kit_type: KitType = KitType.MAIN_WHITE
    product_name: str = "产品"
    selling_points: list[str] = field(default_factory=list)
    brand_tone: str = ""
    api_key: str = ""  # 前端传来的 API key，优先于环境变量


@dataclass(frozen=True)
class ImageGenerationResult:
    path: Path
    provider: str
    prompt: str


class ImageGenerationProvider:
    provider_name = "abstract"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        raise NotImplementedError

    async def inpaint(self, *args, **kwargs) -> ImageGenerationResult:
        raise NotImplementedError("Inpainting is reserved for Phase 2.")


class MockImageGenerationProvider(ImageGenerationProvider):
    provider_name = "mock"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Minimal placeholder — one solid-colour image per kit type."""
        from PIL import Image, ImageColor
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        bg = Image.new("RGB", (request.width, request.height), "#1A1A2E")
        bg.save(request.output_path, "PNG")
        return ImageGenerationResult(
            path=request.output_path,
            provider="mock",
            prompt=request.prompt,
        )


# ═══════════════════════════════════════════════════════════════
#  Real AI Providers
# ═══════════════════════════════════════════════════════════════

import base64
import json
import mimetypes
import os
import subprocess
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class SiliconFlowProvider(ImageGenerationProvider):
    """国内硅基流动 SiliconFlow — OpenAI兼容API，Flux Schnell/Pro 生图。
    
    需要 SILICONFLOW_KEY 环境变量。注册：https://siliconflow.cn
    API 文档：https://docs.siliconflow.cn/api-reference/images/generations
    """

    def __init__(self, model: str = "fast", endpoint: str = "", model_id: str = ""):
        self.model = model
        self.api_key = os.environ.get("SILICONFLOW_KEY", "")
        if model == "fast":
            self.provider_name = "siliconflow-fast"
            self.model_id = model_id or "Tongyi-MAI/Z-Image-Turbo"
        else:
            self.provider_name = "siliconflow-pro"
            self.model_id = model_id or "Tongyi-MAI/Z-Image"
        self.endpoint = endpoint or "https://api.siliconflow.cn/v1/images/generations"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        api_key = request.api_key or self.api_key
        if not api_key:
            raise RuntimeError("SILICONFLOW_KEY environment variable not set. Register at siliconflow.cn")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Encode product image as base64 for img2img reference
        with open(request.product_image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        size = f"{request.width}x{request.height}"
        payload = {
            "model": self.model_id,
            "prompt": request.prompt,
            "image": image_b64,
            "n": 1,
            "size": size,
        }

        req = Request(self.endpoint, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})

        try:
            with urlopen(req, timeout=120, context=ssl_context()) as resp:
                data = json.loads(resp.read())
        except URLError as e:
            raise RuntimeError(f"SiliconFlow request failed: {e}")

        images = data.get("images") or data.get("data", [])
        if not images:
            raise RuntimeError(f"SiliconFlow returned no images: {data}")

        image_url = images[0].get("url") or images[0].get("b64_json")
        if not image_url:
            raise RuntimeError(f"SiliconFlow no URL/b64: {data}")

        try:
            if image_url.startswith("data:"):
                request.output_path.write_bytes(base64.b64decode(image_url.split(",", 1)[1]))
            else:
                img_req = Request(image_url)
                with urlopen(img_req, timeout=60, context=ssl_context()) as r:
                    request.output_path.write_bytes(r.read())
        except URLError as e:
            raise RuntimeError(f"Failed to download image: {e}")

        return ImageGenerationResult(
            path=request.output_path, provider=self.provider_name, prompt=request.prompt)


class FalAiProvider(ImageGenerationProvider):
    """fal.ai REST API provider — supports flux/schnell and flux/pro."""

    def __init__(self, model: str = "fast", endpoint: str = ""):
        self.model = model
        self.api_key = os.environ.get("FAL_KEY", "")
        if model == "fast":
            self.provider_name = "fal-fast"
            self.endpoint = endpoint or "https://fal.run/fal-ai/flux/schnell"
        else:
            self.provider_name = "fal-pro"
            self.endpoint = endpoint or "https://fal.run/fal-ai/flux-pro/v1.1-ultra"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        api_key = request.api_key or self.api_key
        if not api_key:
            raise RuntimeError("FAL_KEY environment variable not set")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare payload
        payload = {
            "prompt": request.prompt,
            "image_size": "square_hd" if request.width == request.height else "landscape_4_3",
            "num_images": 1,
            "enable_safety_checker": False,
        }

        # If product image exists, use img2img endpoint
        if request.product_image_path.exists():
            with open(request.product_image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            payload["image_url"] = f"data:image/png;base64,{img_b64}"
            payload["strength"] = 0.65  # preserve product shape
            # Switch to img2img endpoint
            if self.model == "fast":
                self.endpoint = "https://fal.run/fal-ai/flux/schnell/image-to-image"

        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        # Submit
        try:
            with urlopen(req, timeout=30, context=ssl_context()) as resp:
                submit_data = json.loads(resp.read())
        except URLError as e:
            raise RuntimeError(f"fal.ai request failed: {e}")

        # Poll for result (fal.ai returns a request_id for async)
        request_id = submit_data.get("request_id", "")
        result_url = None
        for _ in range(30):
            time.sleep(2)
            status_req = Request(
                f"https://fal.run/{request_id}/status" if request_id else self.endpoint + "/status",
                headers={"Authorization": f"Key {self.api_key}"},
            )
            try:
                with urlopen(status_req, timeout=10, context=ssl_context()) as resp:
                    data = json.loads(resp.read())
                if data.get("status") == "COMPLETED":
                    images = data.get("images") or data.get("output", {}).get("images", [])
                    if images:
                        result_url = images[0].get("url") or images[0]
                    break
            except Exception:
                continue

        if not result_url:
            raise RuntimeError("fal.ai generation timed out")

        # Download the result
        try:
            img_req = Request(result_url)
            with urlopen(img_req, timeout=30, context=ssl_context()) as resp:
                request.output_path.write_bytes(resp.read())
        except URLError as e:
            raise RuntimeError(f"Failed to download fal.ai image: {e}")

        return ImageGenerationResult(
            path=request.output_path,
            provider=self.provider_name,
            prompt=request.prompt,
        )


class CodexImagegenProvider(ImageGenerationProvider):
    """Codex CLI imagegen provider — uses `codex exec` with async subprocess."""

    provider_name = "codex"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        import asyncio

        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build a concise but rich prompt for Codex
        prompt = (
            f"Generate a product ecommerce image based on this spec:\n"
            f"{request.prompt}\n\n"
            f"Reference product image at: {request.product_image_path}\n"
            f"Output: {request.width}x{request.height}px saved to {request.output_path}\n"
            f"Use imagegen tool. Generate immediately — no explanation needed."
        )

        # Feed prompt via stdin to avoid argument parsing issues
        proc = await asyncio.create_subprocess_exec(
            "codex", "exec", "--yolo",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(request.output_path.parent),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()), timeout=180
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise RuntimeError("Codex generation timed out (180s)")

        stdout_text = stdout.decode() if stdout else ""
        stderr_text = stderr.decode() if stderr else ""

        if proc.returncode != 0:
            raise RuntimeError(
                f"Codex failed (exit {proc.returncode}): {stderr_text[:300]}"
            )

        if not request.output_path.exists():
            raise RuntimeError(
                f"Codex did not produce output at {request.output_path}. "
                f"stdout: {stdout_text[:300]}"
            )

        return ImageGenerationResult(
            path=request.output_path,
            provider=self.provider_name,
            prompt=request.prompt,
        )


class AgnesProvider(ImageGenerationProvider):
    """Agnes AI — 新加坡 Sapiens AI 全模态免费 API。图生图/文生图。

    需要 AGNES_API_KEY 环境变量。注册：https://platform.agnes-ai.com
    API: POST https://apihub.agnes-ai.com/v1/images/generations
    """

    provider_name = "agnes"

    def __init__(self, endpoint: str = "", model_id: str = ""):
        self.api_key = os.environ.get("AGNES_API_KEY", "")
        self.endpoint = endpoint or "https://apihub.agnes-ai.com/v1/images/generations"
        self.model_id = model_id or "agnes-image-2.1-flash"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        api_key = request.api_key or self.api_key
        if not api_key:
            raise RuntimeError(
                "AGNES_API_KEY environment variable not set. "
                "Register for free at https://platform.agnes-ai.com"
            )

        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict = {
            "model": self.model_id,
            "prompt": request.prompt,
            "size": f"{request.width}x{request.height}",
            "extra_body": {
                "response_format": "url"
            }
        }

        # Agnes img2img: image must be in extra_body.image array (per 2.1-flash docs)
        if request.product_image_path.exists():
            with open(request.product_image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode()
            payload["extra_body"]["image"] = [f"data:image/png;base64,{image_b64}"]

        # Write payload to temp file (curl -d @file avoids shell escaping issues)
        import tempfile
        payload_json = json.dumps(payload)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False,
            prefix="agnes_payload_"
        ) as tmp:
            tmp.write(payload_json)
            payload_file = tmp.name

        try:
            # Step 1: POST to Agnes API via curl (auto-follows system proxy)
            proc = await asyncio.create_subprocess_exec(
                "curl", "-s", "-X", "POST", self.endpoint,
                "-H", f"Authorization: Bearer {self.api_key}",
                "-H", "Content-Type: application/json",
                "-d", f"@{payload_file}",
                "--connect-timeout", "30", "--max-time", "120",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=130
            )

            if proc.returncode != 0:
                raise RuntimeError(
                    f"Agnes curl failed (exit {proc.returncode}): {stderr.decode()[:300]}"
                )

            data = json.loads(stdout.decode())

        finally:
            os.unlink(payload_file)

        # Parse response: {"data": [{"url": "..."}]}
        images = data.get("data", [])
        if not images:
            raise RuntimeError(f"Agnes returned no images: {data}")

        image_url = images[0].get("url", "")
        if not image_url:
            raise RuntimeError(f"Agnes no URL in response: {data}")

        # Step 2: Download the generated image via curl
        proc2 = await asyncio.create_subprocess_exec(
            "curl", "-s", "-o", str(request.output_path),
            image_url,
            "--connect-timeout", "30", "--max-time", "60",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc2.communicate(), timeout=70)

        if proc2.returncode != 0 or not request.output_path.exists():
            raise RuntimeError(f"Failed to download Agnes image: {image_url}")

        return ImageGenerationResult(
            path=request.output_path,
            provider=self.provider_name,
            prompt=request.prompt,
        )


class VolcEngineArkProvider(ImageGenerationProvider):
    """火山方舟 Seedream 5.0 — true img2img product generation."""

    provider_name = "volcengine-ark"

    def __init__(self, endpoint: str = "", model_id: str = ""):
        self.api_key = os.environ.get("VOLCENGINE_ARK_API_KEY", "")
        self.endpoint = endpoint or "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        self.model_id = model_id or "doubao-seedream-5-0-260128"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        api_key = request.api_key or self.api_key
        if not api_key:
            raise RuntimeError("VOLCENGINE_ARK_API_KEY environment variable not set")

        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict = {
            "model": self.model_id,
            "prompt": request.prompt,
            "sequential_image_generation": "disabled",
            "response_format": "url",
            "size": self._size_for_request(request.width, request.height),
            "stream": False,
            "watermark": False,
        }

        image_paths = self._image_paths_for_request(request)
        if image_paths:
            image_refs = [self._image_data_url(path) for path in image_paths]
            payload["image"] = image_refs if len(image_refs) > 1 else image_refs[0]

        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urlopen(req, timeout=180, context=ssl_context()) as resp:
                data = json.loads(resp.read())
        except HTTPError as e:
            body = e.read().decode(errors="replace")
            if isinstance(payload.get("image"), list):
                payload["image"] = payload["image"][0]
                data = self._submit_payload(payload)
            else:
                raise RuntimeError(f"VolcEngine Ark request failed ({e.code}): {body[:500]}")
        except URLError as e:
            raise RuntimeError(f"VolcEngine Ark request failed: {e}")

        images = data.get("data") or data.get("images") or []
        if not images:
            raise RuntimeError(f"VolcEngine Ark returned no images: {data}")

        image_ref = images[0].get("url") or images[0].get("b64_json")
        if not image_ref:
            raise RuntimeError(f"VolcEngine Ark no URL/b64 in response: {data}")

        try:
            if image_ref.startswith("data:"):
                request.output_path.write_bytes(base64.b64decode(image_ref.split(",", 1)[1]))
            elif image_ref.startswith(("http://", "https://")):
                img_req = Request(image_ref)
                with urlopen(img_req, timeout=120, context=ssl_context()) as resp:
                    request.output_path.write_bytes(resp.read())
            else:
                request.output_path.write_bytes(base64.b64decode(image_ref))
        except (ValueError, URLError) as e:
            raise RuntimeError(f"Failed to save VolcEngine Ark image: {e}")

        return ImageGenerationResult(
            path=request.output_path,
            provider=self.provider_name,
            prompt=request.prompt,
        )

    def _submit_payload(self, payload: dict):
        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(req, timeout=180, context=ssl_context()) as resp:
            return json.loads(resp.read())

    @staticmethod
    def _image_paths_for_request(request: ImageGenerationRequest) -> list[Path]:
        multi_view = next(
            (path for path in request.reference_image_paths if path.name == "multi_view.png" and path.exists()),
            None,
        )
        if multi_view:
            return [multi_view]

        paths: list[Path] = []
        if request.product_image_path.exists():
            paths.append(request.product_image_path)
        for path in request.reference_image_paths:
            if path.exists() and path not in paths:
                paths.append(path)
        return paths[:6]

    @staticmethod
    def _image_data_url(image_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            suffix = image_path.suffix.lower()
            if suffix in {".jpg", ".jpeg"}:
                mime_type = "image/jpeg"
            elif suffix == ".png":
                mime_type = "image/png"
            elif suffix == ".webp":
                mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"
        image_b64 = base64.b64encode(image_path.read_bytes()).decode()
        return f"data:{mime_type};base64,{image_b64}"

    @staticmethod
    def _size_for_request(width: int, height: int) -> str:
        # Seedream 5.0 API documents 2K and 4K presets for this model.
        return "4K" if max(width, height) > 2048 else "2K"


# ── Provider factory ──────────────────────────────────────────

from app.config.providers import PROVIDER_REGISTRY, ProviderMeta


_CLASS_CACHE: dict[str, type] = {}


def _get_provider_class(class_name: str) -> type:
    """Resolve a provider class name string to the actual class."""
    if class_name in _CLASS_CACHE:
        return _CLASS_CACHE[class_name]
    cls = globals().get(class_name)
    if cls is None:
        raise ValueError(f"Provider class '{class_name}' not found in imagegen.py")
    _CLASS_CACHE[class_name] = cls
    return cls


def _find_meta(name: str) -> ProviderMeta | None:
    for meta in PROVIDER_REGISTRY:
        if meta.name == name:
            return meta
    return None


def create_provider(name: str) -> ImageGenerationProvider:
    """Create a provider instance by name, reading endpoint/model_id from config."""
    if name == "mock":
        # Placeholder: minimal solid-colour fallback, no config needed
        return MockImageGenerationProvider()

    meta = _find_meta(name)
    if meta is None:
        available = [m.name for m in PROVIDER_REGISTRY]
        raise ValueError(
            f"Unknown provider: {name}. Available: mock, {', '.join(available)}"
        )

    cls = _get_provider_class(meta.provider_class)

    # Determine extra kwargs from the provider name convention
    kwargs: dict[str, str] = {}
    if meta.endpoint:
        kwargs["endpoint"] = meta.endpoint
    if meta.model_id:
        kwargs["model_id"] = meta.model_id

    # FalAiProvider and SiliconFlowProvider need a model param
    if name.startswith("fal-") or name.startswith("siliconflow-"):
        kwargs["model"] = name.split("-", 1)[1]  # "fast" or "pro"

    # Only pass kwargs the class actually accepts
    import inspect
    sig = inspect.signature(cls.__init__)
    accepted = set(sig.parameters.keys())
    filtered = {k: v for k, v in kwargs.items() if k in accepted}

    return cls(**filtered)
