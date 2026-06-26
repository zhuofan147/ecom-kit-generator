"""Product image analysis: Vision AI + traditional metrics."""

import base64
import json
import logging
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from PIL import Image

logger = logging.getLogger(__name__)

VISION_PROMPT = """你是一个电商产品图分析专家。请仔细分析这张产品图，输出以下信息的 JSON：

{
  "product_type": "产品类型（如：运动鞋、T恤、手机壳、耳机）",
  "main_color": "主色调",
  "secondary_colors": ["次要颜色1", "次要颜色2"],
  "materials": ["材质1", "材质2"],
  "key_features": ["关键特征1", "关键特征2", "关键特征3"],
  "style": "风格（如：休闲、商务、运动、复古）",
  "target_gender": "适用性别（男/女/中性）",
  "has_logo": true/false,
  "has_text": true/false,
  "brief_description": "一句话产品描述"
}

只输出 JSON，不要 markdown 包裹。"""


def analyze_product_cutout(image_path: Path, llm_api_url: str = "", llm_api_key: str = "", llm_model: str = "") -> dict:
    """Analyze product cutout image: Vision AI + traditional metrics.

    If Vision API (llm_api_key + llm_model) is available, enrich with AI analysis.
    Otherwise fall back to PIL-only metrics.
    """
    # ── traditional PIL analysis ──
    with Image.open(image_path) as image:
        rgba = image.convert("RGBA")
        width, height = rgba.size
        alpha = rgba.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            bbox = (0, 0, width, height)

        subject_w = bbox[2] - bbox[0]
        subject_h = bbox[3] - bbox[1]
        subject = rgba.crop(bbox)
        pixel_iter = (
            subject.get_flattened_data()
            if hasattr(subject, "get_flattened_data")
            else subject.getdata()
        )
        pixels = [pixel[:3] for pixel in pixel_iter if pixel[3] > 24]

    colors = _dominant_colors(pixels)
    coverage = round((subject_w * subject_h) / max(width * height, 1), 3)
    aspect = round(subject_w / max(subject_h, 1), 2)

    result = {
        "canvas_width": width,
        "canvas_height": height,
        "subject_width": subject_w,
        "subject_height": subject_h,
        "subject_aspect": aspect,
        "subject_coverage": coverage,
        "dominant_colors": colors,
        "has_transparent_background": True,
    }

    # ── Vision AI enrichment ──
    if llm_api_key and llm_model:
        try:
            vision_result = _call_vision_api(image_path, llm_api_url, llm_api_key, llm_model)
            if vision_result:
                result["vision_analysis"] = vision_result
                print(f"VISION_OK: {vision_result.get('product_type', '?')} — {vision_result.get('brief_description', '?')[:100]}", flush=True)
        except Exception as e:
            print(f"VISION_FAIL: {e}", flush=True)

    return result


def _call_vision_api(image_path: Path, api_url: str, api_key: str, model: str) -> dict | None:
    """Call OpenAI-compatible Vision API to analyze product image."""
    print(f"VISION_CALL: url={api_url[:40]} model={model} key_len={len(api_key)}", flush=True)
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    # Guess MIME type
    suffix = image_path.suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(
        suffix.lstrip("."), "image/png"
    )

    url = _chat_completions_url(api_url)
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
            ]
        }],
        "max_tokens": 500,
        "temperature": 0.3,
    }

    req = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.time()
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise RuntimeError(f"Vision HTTP {e.code}: {body}")
    except URLError as e:
        raise RuntimeError(f"Vision request failed: {e}")

    elapsed = time.time() - t0
    content = data["choices"][0]["message"]["content"]
    logger.info(f"Vision API responded in {elapsed:.1f}s")

    # Parse JSON response
    try:
        # Strip markdown fences if present
        text = content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.warning(f"Vision returned non-JSON (len={len(content)}): {content[:500]}")
        return {"brief_description": content[:200], "product_type": ""}


def _chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def format_product_image_analysis(analysis: dict | None) -> str:
    if not analysis:
        return "未提供产品图分析。"

    parts = []

    # Vision analysis takes priority
    va = analysis.get("vision_analysis")
    if va and isinstance(va, dict):
        if va.get("brief_description"):
            parts.append(f"产品描述：{va['brief_description']}")
        if va.get("product_type"):
            parts.append(f"产品类型：{va['product_type']}")
        if va.get("materials"):
            parts.append(f"材质：{'、'.join(va['materials'])}")
        if va.get("key_features"):
            parts.append(f"关键特征：{'、'.join(va['key_features'])}")
        if va.get("style"):
            parts.append(f"风格：{va['style']}")
        if va.get("main_color"):
            parts.append(f"主色调：{va['main_color']}")
        if va.get("secondary_colors"):
            parts.append(f"次要颜色：{'、'.join(va['secondary_colors'])}")
        return "\n".join(parts) if parts else "Vision 分析未返回有效信息。"

    # Fallback: PIL metrics only
    colors = analysis.get("dominant_colors") or []
    color_text = "、".join(colors) if colors else "参考图原始色彩"
    lines = [
        f"主色：{color_text}",
        f"产品在画面中占比约 {int(analysis.get('subject_coverage', 0) * 100)}%",
        f"宽高比约 {analysis.get('subject_aspect', '?')}",
    ]
    return "\n".join(lines)


def _dominant_colors(pixels: list, max_colors: int = 5) -> list[str]:
    """Extract dominant color names from pixel data."""
    if not pixels:
        return []
    from collections import Counter
    # Simple: bucket into named colors
    named = []
    for r, g, b in pixels:
        if r > 200 and g > 200 and b > 200:
            named.append("白色")
        elif r < 60 and g < 60 and b < 60:
            named.append("黑色")
        elif r < 80 and g < 80 and b > 120:
            named.append("深蓝")
        elif r > 150 and g < 80 and b < 80:
            named.append("红色")
        elif r > 150 and g > 120 and b < 80:
            named.append("橙黄")
        elif r < 80 and g > 120 and b < 80:
            named.append("绿色")
        elif r < 80 and g > 120 and b > 120:
            named.append("青色")
        else:
            named.append("灰色")
    counter = Counter(named)
    return [color for color, _ in counter.most_common(max_colors)]
