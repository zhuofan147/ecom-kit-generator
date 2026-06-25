"""Lightweight analysis for uploaded cutout product images."""

from pathlib import Path

from PIL import Image


def analyze_product_cutout(image_path: Path) -> dict:
    """Extract stable visual facts from the transparent cutout image."""
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

    return {
        "canvas_width": width,
        "canvas_height": height,
        "subject_width": subject_w,
        "subject_height": subject_h,
        "subject_aspect": aspect,
        "subject_coverage": coverage,
        "dominant_colors": colors,
        "has_transparent_background": True,
    }


def format_product_image_analysis(analysis: dict | None) -> str:
    if not analysis:
        return "未提供抠图产品图分析。"

    colors = analysis.get("dominant_colors") or []
    color_text = "、".join(colors) if colors else "参考图原始色彩"
    return (
        "抠图产品分析：主体尺寸约"
        f"{analysis.get('subject_width', '未知')}x{analysis.get('subject_height', '未知')}px，"
        f"主体宽高比约{analysis.get('subject_aspect', '未知')}，"
        f"主体占画布约{analysis.get('subject_coverage', '未知')}，"
        f"主色调为{color_text}。"
    )


def _dominant_colors(pixels: list[tuple[int, int, int]]) -> list[str]:
    if not pixels:
        return []

    buckets: dict[tuple[int, int, int], int] = {}
    sample_step = max(len(pixels) // 5000, 1)
    for red, green, blue in pixels[::sample_step]:
        bucket = (red // 32 * 32, green // 32 * 32, blue // 32 * 32)
        buckets[bucket] = buckets.get(bucket, 0) + 1

    dominant = sorted(buckets.items(), key=lambda item: item[1], reverse=True)[:4]
    return [f"#{red:02X}{green:02X}{blue:02X}" for (red, green, blue), _ in dominant]
