"""Image generation: abstract provider + mock compositor for all kit types."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

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

    # ── colour palette ──────────────────────────────────────────────
    _SCENE_GRADIENTS = {
        "": ("#E8F4F8", "#D4E6F1"),          # default: soft blue
        "科技感": ("#1A1A2E", "#16213E"),       # dark tech
        "简约": ("#F5F5F5", "#E8E8E8"),         # minimal
        "国潮": ("#C62828", "#8E0000"),          # red
        "北欧": ("#ECEFF1", "#CFD8DC"),          # nordic
        "奢华": ("#1A1A1A", "#3E2723"),          # luxury dark
        "自然": ("#E8F5E9", "#C8E6C9"),          # green
        "少女": ("#FCE4EC", "#F8BBD0"),          # pink
    }

    _USAGE_BG = {
        "办公": ("#ECEFF1", "#B0BEC5"),
        "户外": ("#E8F5E9", "#A5D6A7"),
        "居家": ("#FFF3E0", "#FFCC80"),
        "聚会": ("#F3E5F5", "#CE93D8"),
        "运动": ("#E3F2FD", "#90CAF9"),
    }

    # ── main entry ──────────────────────────────────────────────────
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)

        handlers = {
            KitType.MAIN_WHITE:    self._render_white_bg,
            KitType.MAIN_SCENE:    self._render_scene,
            KitType.SELLING_POINT: self._render_selling_point,
            KitType.SIZE_COMPARE:  self._render_size_compare,
            KitType.DETAIL:        self._render_detail,
            KitType.USAGE_SCENE:   self._render_usage_scene,
            KitType.SKU_VARIANTS:  self._render_sku_variants,
            KitType.DETAIL_PAGE:   self._render_detail_page,
            KitType.CAROUSEL:      self._render_carousel,
            KitType.VIDEO_COVER:   self._render_video_cover,
        }

        handler = handlers.get(request.kit_type, self._render_white_bg)
        canvas = handler(request)
        canvas.save(request.output_path, format="PNG")
        return ImageGenerationResult(
            path=request.output_path,
            provider=self.provider_name,
            prompt=request.prompt,
        )

    # ── helpers ─────────────────────────────────────────────────────
    def _load_product(self, request: ImageGenerationRequest,
                       max_ratio: float = 0.78) -> Image.Image:
        with Image.open(request.product_image_path) as source:
            product = source.convert("RGBA")
            max_w = int(request.width * max_ratio)
            max_h = int(request.height * max_ratio)
            product.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            return product

    def _build_shadow(self, product: Image.Image,
                       color: tuple = (0, 0, 0, 70),
                       radius: int = 14) -> Image.Image:
        alpha = product.getchannel("A")
        shadow = Image.new("RGBA", product.size, color)
        shadow.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius=radius)))
        return shadow

    def _center_paste(self, canvas: Image.Image,
                       product: Image.Image,
                       shadow: Image.Image | None = None) -> tuple[int, int]:
        x = (canvas.width - product.width) // 2
        y = (canvas.height - product.height) // 2
        if shadow:
            sy = min(canvas.height - shadow.height,
                      y + int(product.height * 0.08))
            canvas.alpha_composite(shadow, (x, sy))
        canvas.alpha_composite(product, (x, y))
        return x, y

    def _gradient_bg(self, width: int, height: int,
                      top: str, bottom: str) -> Image.Image:
        """Vertical linear gradient."""
        from PIL import ImageColor
        c1 = ImageColor.getrgb(top)
        c2 = ImageColor.getrgb(bottom)
        img = Image.new("RGBA", (width, height))
        pixels = img.load()
        for y in range(height):
            r = int(round(c1[0] + (c2[0] - c1[0]) * y / (height - 1)))
            g = int(round(c1[1] + (c2[1] - c1[1]) * y / (height - 1)))
            b = int(round(c1[2] + (c2[2] - c1[2]) * y / (height - 1)))
            for x in range(width):
                pixels[x, y] = (r, g, b, 255)
        return img

    @staticmethod
    def _try_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        # macOS system CJK fonts, fallback to default
        for fp in ("/System/Library/Fonts/PingFang.ttc",
                    "/System/Library/Fonts/STHeiti Light.ttc",
                    "/System/Library/Fonts/Hiragino Sans GB.ttc"):
            try:
                return ImageFont.truetype(fp, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    def _draw_text_block(self, draw: ImageDraw.ImageDraw, text: str,
                          x: int, y: int, font_size: int = 20,
                          fill: str = "#333333",
                          max_width: int = 700) -> int:
        font = self._try_font(font_size)
        # simple word wrap for CJK
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            if draw.textbbox((0, 0), test, font=font)[2] > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)

        yy = y
        for line in lines:
            draw.text((x, yy), line, fill=fill, font=font)
            yy += font_size + 6
        return yy

    # ── kit type renderers ──────────────────────────────────────────
    def _render_white_bg(self, r: ImageGenerationRequest) -> Image.Image:
        canvas = Image.new("RGBA", (r.width, r.height), (255, 255, 255, 255))
        product = self._load_product(r)
        shadow = self._build_shadow(product)
        self._center_paste(canvas, product, shadow)
        return canvas.convert("RGB")

    def _render_scene(self, r: ImageGenerationRequest) -> Image.Image:
        gradient = self._SCENE_GRADIENTS.get(r.brand_tone, self._SCENE_GRADIENTS[""])
        bg = self._gradient_bg(r.width, r.height, *gradient)
        product = self._load_product(r)
        shadow = self._build_shadow(product, color=(40, 40, 40, 80), radius=20)
        # place product lower (golden ratio feel)
        x = (r.width - product.width) // 2
        y = int(r.height * 0.55) - product.height // 2
        shadow_y = min(r.height - shadow.height, y + int(product.height * 0.06))
        bg.alpha_composite(shadow, (x, shadow_y))
        bg.alpha_composite(product, (x, y))

        # watermark label
        draw = ImageDraw.Draw(bg)
        font = self._try_font(16)
        draw.text((16, r.height - 28), "[场景主图 · Mock]", fill="#999999", font=font)
        return bg.convert("RGB")

    def _render_selling_point(self, r: ImageGenerationRequest) -> Image.Image:
        canvas = Image.new("RGBA", (r.width, r.height), (255, 255, 255, 255))
        product = self._load_product(r, max_ratio=0.65)
        shadow = self._build_shadow(product)
        self._center_paste(canvas, product, shadow)

        draw = ImageDraw.Draw(canvas)
        # product name
        name_font = self._try_font(28)
        tw = draw.textbbox((0, 0), r.product_name, font=name_font)[2]
        draw.text(((r.width - tw) // 2, r.height - 140),
                   r.product_name, fill="#1A1A1A", font=name_font)

        # selling points
        sp_font = self._try_font(18)
        y = r.height - 100
        for pt in r.selling_points[:3]:
            text = f"✓ {pt}"
            lw = draw.textbbox((0, 0), text, font=sp_font)[2]
            draw.text(((r.width - lw) // 2, y), text, fill="#555555", font=sp_font)
            y += 26

        # watermark
        wm = self._try_font(14)
        draw.text((16, r.height - 22), "[卖点主图 · Mock]", fill="#CCCCCC", font=wm)
        return canvas.convert("RGB")

    def _render_size_compare(self, r: ImageGenerationRequest) -> Image.Image:
        canvas = Image.new("RGBA", (r.width, r.height), (250, 250, 250, 255))
        product = self._load_product(r, max_ratio=0.45)

        # draw a reference rectangle (phone/card sized)
        ref_w, ref_h = 80, 160
        ref = Image.new("RGBA", (ref_w, ref_h), (200, 200, 200, 200))
        ref_draw = ImageDraw.Draw(ref)
        ref_draw.rectangle([0, 0, ref_w - 1, ref_h - 1], outline=(150, 150, 150), width=2)

        product_x = r.width // 2 - product.width - 40
        product_y = (r.height - product.height) // 2
        ref_x = r.width // 2 + 40
        ref_y = (r.height - ref_h) // 2

        shadow = self._build_shadow(product, radius=12)
        canvas.alpha_composite(shadow, (product_x, product_y + int(product.height * 0.06)))
        canvas.alpha_composite(product, (product_x, product_y))
        canvas.alpha_composite(ref, (ref_x, ref_y))

        # dimension lines
        draw = ImageDraw.Draw(canvas)
        font = self._try_font(14)
        draw.text((product_x, product_y - 22), "产品", fill="#666", font=font)
        draw.text((ref_x, ref_y - 22), "iPhone 参照", fill="#666", font=font)
        draw.text((16, r.height - 24), "[尺寸对比图 · Mock]", fill="#AAA", font=font)

        return canvas.convert("RGB")

    def _render_detail(self, r: ImageGenerationRequest) -> Image.Image:
        canvas = Image.new("RGBA", (r.width, r.height), (255, 255, 255, 255))
        with Image.open(r.product_image_path) as source:
            product = source.convert("RGBA")
            # crop center 60% → zoom to fill
            cw, ch = int(product.width * 0.6), int(product.height * 0.6)
            cx = (product.width - cw) // 2
            cy = (product.height - ch) // 2
            crop = product.crop((cx, cy, cx + cw, cy + ch))
            crop = crop.resize((r.width, r.height), Image.Resampling.LANCZOS)

        draw = ImageDraw.Draw(crop)
        font = self._try_font(16)
        draw.text((16, r.height - 28), "[细节特写图 · Mock]", fill="#999999", font=font)
        return crop.convert("RGB")

    def _render_usage_scene(self, r: ImageGenerationRequest) -> Image.Image:
        bg = self._gradient_bg(r.width, r.height, "#F5F5F5", "#E0E0E0")
        product = self._load_product(r, max_ratio=0.6)
        shadow = self._build_shadow(product, color=(50, 50, 50, 90), radius=22)

        x = (r.width - product.width) // 2
        y = int(r.height * 0.45) - product.height // 2
        bg.alpha_composite(shadow, (x, y + int(product.height * 0.08)))
        bg.alpha_composite(product, (x, y))

        draw = ImageDraw.Draw(bg)
        font = self._try_font(16)
        draw.text((16, r.height - 28), "[使用场景图 · Mock]", fill="#999", font=font)
        return bg.convert("RGB")

    def _render_sku_variants(self, r: ImageGenerationRequest) -> Image.Image:
        import random
        canvas = Image.new("RGBA", (r.width, r.height), (255, 255, 255, 255))
        product = self._load_product(r, max_ratio=0.30)

        # tint colours for mock variants
        tints = [(255, 220, 220), (220, 255, 220), (220, 220, 255),
                  (255, 255, 200), (255, 220, 255)]
        random.shuffle(tints)

        rows, cols = 2, 3
        cell_w, cell_h = r.width // cols, r.height // rows
        label_colors = ["珊瑚粉", "薄荷绿", "天空蓝", "香槟金", "薰衣紫", "经典白"]

        for i in range(min(6, len(tints) + 1)):
            row, col = divmod(i, cols)
            px = col * cell_w + (cell_w - product.width) // 2
            py = row * cell_h + (cell_h - product.height) // 2 - 12

            # tint
            variant = product.copy()
            if i > 0:
                t = tints[i - 1]
                overlay = Image.new("RGBA", variant.size, (t[0], t[1], t[2], 60))
                variant.alpha_composite(overlay, (0, 0))
            canvas.alpha_composite(variant, (px, py))

            # label
            draw = ImageDraw.Draw(canvas)
            font = self._try_font(13)
            label = label_colors[i]
            tw = draw.textbbox((0, 0), label, font=font)[2]
            draw.text((col * cell_w + (cell_w - tw) // 2,
                        row * cell_h + cell_h - 32),
                       label, fill="#444", font=font)

        draw = ImageDraw.Draw(canvas)
        wm = self._try_font(14)
        draw.text((12, r.height - 22), "[款式 SKU 图 · Mock]", fill="#CCC", font=wm)
        return canvas.convert("RGB")

    def _render_detail_page(self, r: ImageGenerationRequest) -> Image.Image:
        canvas = Image.new("RGBA", (r.width, r.height), (255, 255, 255, 255))
        product = self._load_product(r, max_ratio=0.50)
        sections = r.height // 500

        draw = ImageDraw.Draw(canvas)
        title_font = self._try_font(36)
        body_font = self._try_font(20)

        # header
        draw.rectangle([0, 0, r.width, 100], fill=(30, 30, 30, 255))
        hdr = f"产品详情 · {r.product_name}"
        tw = draw.textbbox((0, 0), hdr, font=title_font)[2]
        draw.text(((r.width - tw) // 2, 28), hdr, fill="#FFFFFF", font=title_font)

        # hero section
        x = (r.width - product.width) // 2
        canvas.alpha_composite(product, (x, 140))

        y = 140 + product.height + 40
        for i in range(sections):
            sec_y = y + i * 320
            if sec_y > r.height - 100:
                break
            draw.rectangle([40, sec_y, r.width - 40, sec_y + 240],
                            outline=(220, 220, 220), width=1)
            draw.text((60, sec_y + 20),
                       f"板块 {i + 1}: 功能特点 / 规格参数 / 展示图",
                       fill="#444", font=body_font)

        wm = self._try_font(14)
        draw.text((16, r.height - 24), "[详情页长图 · Mock]", fill="#CCC", font=wm)
        return canvas.convert("RGB")

    def _render_carousel(self, r: ImageGenerationRequest) -> Image.Image:
        gradient = self._SCENE_GRADIENTS.get(
            r.brand_tone, ("#1A237E", "#283593"))
        bg = self._gradient_bg(r.width, r.height, *gradient)
        product = self._load_product(r, max_ratio=0.38)

        # right side product
        px = int(r.width * 0.62)
        py = (r.height - product.height) // 2
        sh = self._build_shadow(product, color=(0, 0, 0, 100), radius=24)
        bg.alpha_composite(sh, (px, py + int(product.height * 0.06)))
        bg.alpha_composite(product, (px, py))

        # left side text
        draw = ImageDraw.Draw(bg)
        title_f = self._try_font(42)
        sub_f = self._try_font(22)
        draw.text((60, r.height // 2 - 50), r.product_name, fill="#FFFFFF", font=title_f)
        self._draw_text_block(draw, "首发特惠 · 限时抢购", 60, r.height // 2 + 10,
                               font_size=22, fill="#FFD54F", max_width=500)
        wm = self._try_font(13)
        draw.text((16, r.height - 22), "[轮播图 · Mock]", fill="#999", font=wm)
        return bg.convert("RGB")

    def _render_video_cover(self, r: ImageGenerationRequest) -> Image.Image:
        gradient = self._SCENE_GRADIENTS.get(r.brand_tone, ("#263238", "#37474F"))
        bg = self._gradient_bg(r.width, r.height, *gradient)
        product = self._load_product(r, max_ratio=0.4)
        shadow = self._build_shadow(product, color=(0, 0, 0, 120), radius=28)

        self._center_paste(bg, product, shadow)

        # overlay text
        draw = ImageDraw.Draw(bg)
        title_f = self._try_font(48)
        sub_f = self._try_font(24)
        name = r.product_name
        tw = draw.textbbox((0, 0), name, font=title_f)[2]
        draw.text(((r.width - tw) // 2, 60), name,
                   fill="#FFFFFF", font=title_f)
        tag = "开箱评测 · 深度体验"
        tw2 = draw.textbbox((0, 0), tag, font=sub_f)[2]
        draw.text(((r.width - tw2) // 2, 120), tag,
                   fill="#FFD54F", font=sub_f)

        # play button
        draw.ellipse([r.width // 2 - 40, r.height // 2 - 40,
                       r.width // 2 + 40, r.height // 2 + 40],
                      outline="#FFFFFF", width=4)
        draw.polygon([r.width // 2 - 12, r.height // 2 - 20,
                       r.width // 2 - 12, r.height // 2 + 20,
                       r.width // 2 + 20, r.height // 2],
                      fill="#FFFFFF")

        wm = self._try_font(13)
        draw.text((16, r.height - 22), "[视频封面 · Mock]", fill="#AAA", font=wm)
        return bg.convert("RGB")


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

    def __init__(self, model: str = "fast"):
        self.model = model
        self.api_key = os.environ.get("SILICONFLOW_KEY", "")
        if model == "fast":
            self.provider_name = "siliconflow-fast"
            self.model_id = "Tongyi-MAI/Z-Image-Turbo"
        else:
            self.provider_name = "siliconflow-pro"
            self.model_id = "Tongyi-MAI/Z-Image"
        self.endpoint = "https://api.siliconflow.cn/v1/images/generations"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.api_key:
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

    def __init__(self, model: str = "fast"):
        self.model = model
        self.api_key = os.environ.get("FAL_KEY", "")
        if model == "fast":
            self.provider_name = "fal-fast"
            self.endpoint = "https://fal.run/fal-ai/flux/schnell"
        else:
            self.provider_name = "fal-pro"
            self.endpoint = "https://fal.run/fal-ai/flux-pro/v1.1-ultra"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.api_key:
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

    def __init__(self):
        self.api_key = os.environ.get("AGNES_API_KEY", "")
        self.endpoint = "https://apihub.agnes-ai.com/v1/images/generations"
        self.model_id = "agnes-image-2.1-flash"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.api_key:
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

    def __init__(self):
        self.api_key = os.environ.get("VOLCENGINE_ARK_API_KEY", "")
        self.endpoint = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        self.model_id = "doubao-seedream-5-0-260128"

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not self.api_key:
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

def create_provider(name: str) -> ImageGenerationProvider:
    """Create a provider instance by name."""
    if name == "mock":
        return MockImageGenerationProvider()
    elif name == "fal-fast":
        return FalAiProvider(model="fast")
    elif name == "fal-pro":
        return FalAiProvider(model="pro")
    elif name == "codex":
        return CodexImagegenProvider()
    elif name == "siliconflow-fast":
        return SiliconFlowProvider(model="fast")
    elif name == "siliconflow-pro":
        return SiliconFlowProvider(model="pro")
    elif name == "agnes":
        return AgnesProvider()
    elif name == "volcengine-ark":
        return VolcEngineArkProvider()
    else:
        raise ValueError(
            f"Unknown provider: {name}. Available: mock, fal-fast, fal-pro, "
            f"codex, siliconflow-fast, siliconflow-pro, agnes, volcengine-ark"
        )
