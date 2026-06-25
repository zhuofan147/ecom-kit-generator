"""Rule-based product plan engine for ecommerce image kits."""

import re

from pydantic import BaseModel, Field

from app.config.copy_templates import (
    COPY_TEMPLATES,
    DEFAULT_CATEGORY,
    SELLING_POINT_BUCKETS,
    VISUAL_TEMPLATES,
)
from app.services.template_engine import (
    KIT_LABELS,
    KitType,
    ProductInfo,
    build_prompt,
    build_review_prompt,
    get_platform_rule,
)
from app.services.product_image_analysis import format_product_image_analysis
from app.services.http_client import ssl_context

import json
import logging
import os
import time
from enum import Enum
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)


class PlanRequest(BaseModel):
    product_id: str = ""
    product_name: str
    product_dimensions: str = ""
    product_price: str = ""
    target_audience: str = ""
    usage_scene: str = ""
    selling_points: str = ""
    competitor_diff: str = ""
    platform: str = "taobao"
    kit_types: list[str] = Field(default_factory=list)
    kit_sizes: dict[str, dict[str, int]] = Field(default_factory=dict)
    product_image_analysis: dict = Field(default_factory=dict)
    image_provider: str = "agnes"


class ImagePlan(BaseModel):
    index: int
    main_title: str
    subtitle: str
    visual_suggestion: str
    ai_prompt: str
    kit_type: str


class ProductPlan(BaseModel):
    refined_selling_points: list[str] = Field(default_factory=list)
    image_plans: list[ImagePlan] = Field(default_factory=list)
    mobile_checklist: list[str] = Field(default_factory=list)
    conversion_checklist: list[str] = Field(default_factory=list)
    # ── 知乎文章 §08 通用模板 9 项输出 ──
    universal_template: dict = Field(default_factory=lambda: {
        "core_goal": "",
        "user_understanding": "",
        "main_title": "",
        "scene_elements": [],
        "product_position": "",
        "text_white_space": "",
        "full_prompt": "",
        "avoid_list": [],
        "review_checklist": [],
    })



class PlanEngineMode(str, Enum):
    RULE = "rule"
    AI = "ai"


def _get_plan_engine_mode() -> PlanEngineMode:
    mode = os.environ.get("PLAN_ENGINE_MODE", "ai")
    if mode == "rule":
        return PlanEngineMode.RULE
    return PlanEngineMode.AI


def _get_plan_ai_client():
    """Get AI client for OpenAI-compatible plan generation."""
    tokenplan_key = os.environ.get("TOKENPLAN_API_KEY") or os.environ.get("PLAN_AI_API_KEY", "")
    tokenplan_base_url = os.environ.get("TOKENPLAN_BASE_URL") or os.environ.get("PLAN_AI_BASE_URL", "")
    if tokenplan_key:
        return tokenplan_key, tokenplan_base_url or "https://api.scnet.cn/api/llm/v1", "glm-5.2"

    sf_key = os.environ.get("SILICONFLOW_KEY", "")
    if sf_key:
        return sf_key, "https://api.siliconflow.cn", "zai-org/GLM-5.2"
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    return api_key, base_url, "deepseek-chat"


def _build_chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


_AI_PLAN_SYSTEM_PROMPT = """你是一个顶级电商图生图套图策划专家。

你的任务：根据模板框架 + 产品信息 + 用户输入，生成每种套图类型的第2层场景指令。

工作方式：
1. 读取下方的模板框架，理解每种套图类型的结构
2. 读取产品分析信息（颜色/材质/品类/尺寸）— 仅用于理解产品，不写入 prompt
3. 读取用户输入（卖点/场景偏好/尺寸数据）— 有则用，无则根据产品分析提炼
4. 基于模板填空，将模板中的 [占位符] 替换为具体内容，可增加细节但不改变结构
5. 布光/相机参数/占比等技术参数保持模板原样

禁止：
- 描述产品外观（颜色/材质/形状）→ 靠参考图
- 使用否定词（no/don't/without）
- 写画质标签（8k/masterpiece）→ 系统第3层统一加
- 改变模板结构

## 语言选择
- 如果目标生图模型是 Codex / Agnes / Flux，prompt 必须用英文写。
- 如果目标生图模型是中文模型，prompt 用中文写。
- 你会被告知当前使用的生图模型类型。

## 卖点处理规则
- 如果用户提供了卖点信息（selling_points 非空），你必须结合产品图分析，融合用户卖点生成更有针对性的标注方案，不要简单复制用户原话。
- 如果用户未提供卖点，你必须通过产品图分析提炼3-5个核心卖点（如材质、做工、设计亮点、功能特征等）。

## 尺寸处理规则
- 如果用户提供了尺寸信息（在selling_points或其他字段中包含具体尺寸数值），你必须将这些尺寸融合到detail和size_compare类型的prompt中。
- 如果用户未提供尺寸，你必须根据产品类型和产品图分析估算合理尺寸范围，并写入detail和size_compare的prompt中。
- 尺寸标注应包含具体数值（如"约158mm × 78mm × 12mm"或"approx. 158mm x 78mm x 12mm"）。

## 模板框架：
- white_bg / 白底主图:
{template_white_bg}
- selling_point / 卖点主图:
{template_selling_point}
- scene / 场景主图:
{template_scene}
- detail / 细节特写:
{template_detail}
- size_compare / 尺寸对比:
{template_size_compare}
- use_scene / 使用场景:
{template_use_scene}

## prompt格式要求：
- ai_prompt 只写第2层场景指令，不写第1层产品锁定句，不写第3层收敛句。
- 必须基于对应模板填空，不改变结构。
- 保留模板中的布光/相机参数/占比等技术参数。
- 禁止使用DONT/DON'T/DO NOT/no/without等否定指令，用正面引导。
- 禁止重新描述产品外观特征（颜色/材质/形状），靠参考图传递。

输出格式必须为严格JSON，不要任何markdown标记：
{
  "refined_selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5"],
  "image_plans": [
    {
      "index": 1,
      "main_title": "标题(<=8字)",
      "subtitle": "副标题(<=15字)",
      "visual_suggestion": "画面描述",
      "ai_prompt": "第2层场景指令",
      "kit_type": "main_white"
    },
    ...
  ],
  "mobile_checklist": ["移动端检查项"],
  "conversion_checklist": ["转化率检查项"]
}

kit_type必须使用请求中的类型值并保持顺序。
"""

TEMPLATE_WHITE_BG = """[PRODUCT] centered, occupying 70-80% of frame. Pure white background RGB(255,255,255). Professional studio lighting: top softbox + dual side fill lights, even and soft, no hard shadows. Natural soft shadow beneath product. Front view, eye-level. Commercial product photography style."""

TEMPLATE_SELLING_POINT = """[PRODUCT] centered. [GRADIENT_COLOR] gradient background. Annotation arrows pointing to: [SELLING_POINT_1], [SELLING_POINT_2], [SELLING_POINT_3]. Callout boxes with clean text layout, whitespace around each annotation. 45-degree side lighting, natural shadow. High-end commercial feel."""

TEMPLATE_SCENE = """[PRODUCT] placed in [SCENE_DESC]. Surrounding props: [PROPS] to build atmosphere. Product remains visual center. Scene title "[TITLE]" at top-left. 85mm f/1.4, shallow depth of field, warm natural lighting."""

TEMPLATE_DETAIL = """Zoom-in on [DETAIL_AREA_1] and [DETAIL_AREA_2] of [PRODUCT]. 10x magnification. Highlight [CRAFTSMANSHIP: stitching/texture/material transition]. Soft side lighting to reveal texture. Material label "[MATERIAL_LABEL]". Pure white background."""

TEMPLATE_SIZE_COMPARE = """[PRODUCT] beside [REFERENCE_OBJECT: iPhone 15 Pro / A4 paper / adult hand] for scale. Bottom-aligned. Dimension annotations: "[DIMENSIONS]". Pure white background, top-down view, even lighting. Product edges sharp, proportions accurate."""

TEMPLATE_USE_SCENE = """Person [ACTION] [PRODUCT] in [SCENE_DESC]. Natural hand-to-product contact. Scene caption "[CAPTION]" at bottom. Candid photography style, 35mm lens, natural lighting."""

_AI_PLAN_SYSTEM_PROMPT = (
    _AI_PLAN_SYSTEM_PROMPT
    .replace("{template_white_bg}", TEMPLATE_WHITE_BG)
    .replace("{template_selling_point}", TEMPLATE_SELLING_POINT)
    .replace("{template_scene}", TEMPLATE_SCENE)
    .replace("{template_detail}", TEMPLATE_DETAIL)
    .replace("{template_size_compare}", TEMPLATE_SIZE_COMPARE)
    .replace("{template_use_scene}", TEMPLATE_USE_SCENE)
)

PLAN_KIT_SEQUENCE = [
    KitType.MAIN_WHITE,
    KitType.SELLING_POINT,
    KitType.MAIN_SCENE,
    KitType.DETAIL,
    KitType.USAGE_SCENE,
]


def build_layer1() -> str:
    return "Use the exact product from the reference image. Maintain product consistency including material, color, and shape."


def build_layer3() -> str:
    return "Photorealistic product photography, 8k, e-commerce quality, sharp and clean."


def get_template(kit_type) -> str:
    value = kit_type.value if isinstance(kit_type, KitType) else str(kit_type or "")
    label = value.strip()
    mapping = {
        "white_bg": TEMPLATE_WHITE_BG,
        "main_white": TEMPLATE_WHITE_BG,
        "白底主图": TEMPLATE_WHITE_BG,
        "selling_point": TEMPLATE_SELLING_POINT,
        "卖点主图": TEMPLATE_SELLING_POINT,
        "scene": TEMPLATE_SCENE,
        "main_scene": TEMPLATE_SCENE,
        "场景主图": TEMPLATE_SCENE,
        "detail": TEMPLATE_DETAIL,
        "细节特写": TEMPLATE_DETAIL,
        "细节特写图": TEMPLATE_DETAIL,
        "size_compare": TEMPLATE_SIZE_COMPARE,
        "尺寸对比": TEMPLATE_SIZE_COMPARE,
        "尺寸对比图": TEMPLATE_SIZE_COMPARE,
        "use_scene": TEMPLATE_USE_SCENE,
        "usage_scene": TEMPLATE_USE_SCENE,
        "使用场景": TEMPLATE_USE_SCENE,
        "使用场景图": TEMPLATE_USE_SCENE,
    }
    return mapping.get(label, TEMPLATE_SCENE)


def selected_plan_kit_types(request: PlanRequest) -> list[KitType]:
    selected: list[KitType] = []
    for raw in request.kit_types:
        try:
            kit_type = KitType(raw)
        except ValueError:
            continue
        if kit_type not in selected:
            selected.append(kit_type)
    return selected or PLAN_KIT_SEQUENCE


def plan_size_override(request: PlanRequest, kit_type: KitType) -> tuple[int, int] | None:
    raw_size = request.kit_sizes.get(kit_type.value)
    if not isinstance(raw_size, dict):
        return None
    width = raw_size.get("w")
    height = raw_size.get("h")
    if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
        return width, height
    return None


def detect_category(request: PlanRequest) -> str:
    text = " ".join([
        request.product_name,
        request.target_audience,
        request.usage_scene,
        request.selling_points,
        request.competitor_diff,
    ]).lower()
    for category, template in COPY_TEMPLATES.items():
        if any(keyword.lower() in text for keyword in template["keywords"]):
            return category
    return DEFAULT_CATEGORY


def refine_selling_points(request: PlanRequest, category: str) -> list[str]:
    raw_points = split_points(request.selling_points)
    if request.competitor_diff:
        raw_points.extend(split_points(request.competitor_diff))

    buckets: dict[str, list[str]] = {name: [] for name in SELLING_POINT_BUCKETS}
    for point in raw_points:
        matched = False
        for bucket, keywords in SELLING_POINT_BUCKETS.items():
            if any(keyword in point for keyword in keywords):
                buckets[bucket].append(point)
                matched = True
                break
        if not matched:
            buckets["功能"].append(point)

    ordered_angles = COPY_TEMPLATES[category]["angles"]
    refined = []
    for angle in ordered_angles:
        point = buckets.get(angle, [])
        if point:
            refined.append(format_point(angle, point.pop(0)))

    fallback_points = [point for points in buckets.values() for point in points]
    while len(refined) < 5 and fallback_points:
        refined.append(format_point("卖点", fallback_points.pop(0)))

    defaults = default_points(request, category)
    while len(refined) < 5:
        refined.append(defaults[len(refined)])

    return [truncate_text(point, 18) for point in refined[:5]]


def split_points(text: str) -> list[str]:
    parts = re.split(r"[\n,，;；、]+", text or "")
    return [part.strip() for part in parts if part.strip()]


def format_point(angle: str, point: str) -> str:
    clean = re.sub(r"\s+", "", point)
    if clean.startswith(angle):
        return clean
    return f"{angle}：{clean}"


def default_points(request: PlanRequest, category: str) -> list[str]:
    product = request.product_name or "产品"
    scene = request.usage_scene or "日常使用"
    audience = request.target_audience or "目标用户"
    price = request.product_price or "当前价"
    return [
        f"功能：{product}核心功能清楚",
        f"体验：{audience}使用更省心",
        f"场景：适合{scene}",
        f"性价比：{price}档选择",
        f"外观：{category}质感在线",
    ]


def build_visual_suggestion(
    request: PlanRequest,
    category: str,
    kit_type: KitType,
    angle: str,
    point: str,
) -> str:
    visual = VISUAL_TEMPLATES[category]
    kit_label = KIT_LABELS[kit_type]
    scene = request.usage_scene or "日常使用场景"
    return (
        f"{kit_label}：{visual['composition']}；色调{visual['tone']}；"
        f"围绕{angle}角度展示“{point}”，场景参考：{scene}。"
    )


def _prompt_size(request: PlanRequest, kit_type: KitType) -> tuple[int, int]:
    override_size = plan_size_override(request, kit_type)
    if override_size:
        return override_size
    return base_prompt_size(request.platform, kit_type)


def _prompt_size_text(request: PlanRequest, kit_type: KitType) -> str:
    width, height = _prompt_size(request, kit_type)
    if width > 0 and height > 0:
        return f"{width}x{height}px"
    return "平台默认尺寸"


def _plain_point_text(point: str) -> str:
    return re.sub(r"^[^：:]{1,8}[：:]", "", point or "").strip() or point


def _selling_point_labels(refined_points: list[str]) -> list[str]:
    labels = [_plain_point_text(point) for point in refined_points if point]
    defaults = ["Core benefit", "Key detail", "Everyday use"]
    while len(labels) < 3:
        labels.append(defaults[len(labels)])
    return labels[:5]


def _detail_regions(request: PlanRequest, refined_points: list[str]) -> list[str]:
    text = " ".join([request.product_name, request.selling_points, request.competitor_diff]).lower()
    regions: list[str] = []
    if any(keyword in text for keyword in ["type-c", "接口", "充电", "快充", "usb"]):
        regions.append("charging port or interface alignment")
    if any(keyword in text for keyword in ["按键", "按钮", "button", "键"]):
        regions.append("button fit and tactile area")
    if any(keyword in text for keyword in ["镜头", "摄像", "camera", "lens"]):
        regions.append("camera or lens protection edge")
    if any(keyword in text for keyword in ["防摔", "缓震", "保护", "耐用", "密封"]):
        regions.append("protective edge and reinforced corner")
    if any(keyword in text for keyword in ["材质", "质感", "面料", "纹理", "手感", "做工"]):
        regions.append("surface material texture and craftsmanship")

    fallback = [
        "surface material texture",
        "edge craftsmanship",
        "interface or opening alignment",
        "functional detail area",
    ]
    for item in fallback:
        if len(regions) >= 4:
            break
        if item not in regions:
            regions.append(item)
    return regions[:4]


def _detail_regions_cn(request: PlanRequest, refined_points: list[str]) -> list[str]:
    text = " ".join([request.product_name, request.selling_points, request.competitor_diff]).lower()
    regions: list[str] = []
    if any(keyword in text for keyword in ["type-c", "接口", "充电", "快充", "usb"]):
        regions.append("接口/充电口对齐")
    if any(keyword in text for keyword in ["按键", "按钮", "button", "键"]):
        regions.append("按键贴合与触感区域")
    if any(keyword in text for keyword in ["镜头", "摄像", "camera", "lens"]):
        regions.append("镜头保护边缘")
    if any(keyword in text for keyword in ["防摔", "缓震", "保护", "耐用", "密封"]):
        regions.append("防护边角与缓震结构")
    if any(keyword in text for keyword in ["材质", "质感", "面料", "纹理", "手感", "做工"]):
        regions.append("材质纹理与做工细节")

    fallback = ["材质纹理", "边缘做工", "功能细节区域", "表面高光质感"]
    for item in fallback:
        if len(regions) >= 4:
            break
        if item not in regions:
            regions.append(item)
    return regions[:4]


def _sanitize_prompt_fragment(text: str) -> str:
    text = re.sub(r"\bDONT\b|\bDON'T\b|\bDO NOT\b", "", text or "", flags=re.IGNORECASE)
    text = re.sub(r"\bwithout\b|\bno\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _get_prompt_language(provider: str = "agnes") -> str:
    """Determine prompt language based on image provider."""
    if provider.lower() in ("codex", "agnes", "flux"):
        return "en"
    return "zh"


def _selling_point_labels_en(refined_points: list[str]) -> list[str]:
    """English selling point labels for English providers."""
    has_chinese = any(any('\u4e00' <= c <= '\u9fff' for c in p) for p in refined_points)
    if has_chinese:
        return ["Core benefit", "Key detail", "Material quality", "Design highlight", "Everyday use"]
    labels = [_plain_point_text(point) for point in refined_points if point]
    defaults = ["Core benefit", "Key detail", "Everyday use"]
    while len(labels) < 3:
        labels.append(defaults[len(labels)])
    return labels[:5]


def build_kit_type_prompt(
    request: PlanRequest,
    kit_type: KitType,
    refined_points: list[str],
    visual_suggestion: str = "",
    ai_prompt: str = "",
) -> str:
    """Build a v3 three-layer prompt using the template framework."""
    layer2 = _fill_template_layer2(request, kit_type, refined_points)
    return fuse_final_plan_prompt(kit_type.value, layer2)


def _fill_template_layer2(request: PlanRequest, kit_type: KitType, refined_points: list[str]) -> str:
    template = get_template(kit_type)
    labels = _selling_point_labels_en(refined_points)
    regions = _detail_regions(request, refined_points)
    scene = _sanitize_prompt_fragment(request.usage_scene) or "a clean lifestyle setting"
    title = _sanitize_prompt_fragment(request.product_name) or "Product Highlight"
    dimensions = _extract_dimension_text(request) or "estimated scale from the reference product"
    replacements = {
        "[PRODUCT]": "The product from the reference image",
        "[GRADIENT_COLOR]": "matching the product's natural color from the reference image",
        "[SELLING_POINT_1]": labels[0],
        "[SELLING_POINT_2]": labels[1],
        "[SELLING_POINT_3]": labels[2],
        "[SCENE_DESC]": scene,
        "[PROPS]": "minimal contextual props",
        "[TITLE]": title,
        "[DETAIL_AREA_1]": regions[0],
        "[DETAIL_AREA_2]": regions[1] if len(regions) > 1 else "key functional detail",
        "[CRAFTSMANSHIP: stitching/texture/material transition]": "texture and material transition",
        "[MATERIAL_LABEL]": "Material Detail",
        "[REFERENCE_OBJECT: iPhone 15 Pro / A4 paper / adult hand]": "adult hand",
        "[DIMENSIONS]": dimensions,
        "[ACTION]": "naturally using",
        "[CAPTION]": title,
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def _extract_dimension_text(request: PlanRequest) -> str:
    if request.product_dimensions:
        return request.product_dimensions.strip()

    text = " ".join([
        request.selling_points or "",
        request.competitor_diff or "",
    ])
    match = re.search(
        r"(\d+(?:\.\d+)?\s*(?:mm|cm|m|in|inch|英寸|毫米|厘米)\s*(?:[x×*]\s*\d+(?:\.\d+)?\s*(?:mm|cm|m|in|inch|英寸|毫米|厘米)?){0,2})",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def fuse_final_plan_prompt(
    request: PlanRequest | str,
    kit_type: KitType | str | None = None,
    title: str = "",
    subtitle: str = "",
    visual_suggestion: str = "",
    ai_prompt: str = "",
) -> str:
    if isinstance(request, PlanRequest):
        ai_generated_scene = ai_prompt or visual_suggestion or get_template(kit_type)
    else:
        ai_generated_scene = str(kit_type or "")
    layer1 = build_layer1()
    layer3 = build_layer3()
    return f"{layer1} {ai_generated_scene} {layer3}"


def base_prompt_size(platform: str, kit_type: KitType) -> tuple[int, int]:
    match = re.search(r"(\d+)x(\d+)", build_prompt(platform, kit_type, ProductInfo()))
    if match:
        return int(match.group(1)), int(match.group(2))
    return (0, 0)


def truncate_text(text: str, max_length: int) -> str:
    normalized = re.sub(r"\s+", "", text or "")
    return normalized[:max_length]


def create_product_plan(request: PlanRequest) -> ProductPlan:
    """Unified entry: routes to AI or rule mode based on PLAN_ENGINE_MODE."""
    mode = _get_plan_engine_mode()
    if mode == PlanEngineMode.AI:
        try:
            return create_product_plan_ai(request)
        except Exception as e:
            logger.warning(f"AI plan generation failed, falling back to rule mode: {e}")
            return _create_product_plan_rule(request)
    return _create_product_plan_rule(request)


def _create_product_plan_rule(request: PlanRequest) -> ProductPlan:
    """Rule-based implementation using kit-specific img2img prompt strategies."""
    rule = get_platform_rule(request.platform)
    category = detect_category(request)
    refined_points = refine_selling_points(request, category)
    template = COPY_TEMPLATES[category]

    image_plans = []
    plan_kit_types = selected_plan_kit_types(request)
    for idx, kit_type in enumerate(plan_kit_types, start=1):
        angle = template["angles"][(idx - 1) % len(template["angles"])]
        point = refined_points[(idx - 1) % len(refined_points)]
        title = truncate_text(
            template["title_templates"][(idx - 1) % len(template["title_templates"])],
            8,
        )
        subtitle = truncate_text(
            template["subtitle_templates"][(idx - 1) % len(template["subtitle_templates"])].format(
                product_name=request.product_name or "产品",
                price=request.product_price or "当前价",
                audience=request.target_audience or "目标用户",
                usage_scene=request.usage_scene or "日常场景",
            ),
            15,
        )
        visual = build_visual_suggestion(request, category, kit_type, angle, point)
        prompt = build_kit_type_prompt(
            request=request,
            kit_type=kit_type,
            refined_points=refined_points,
            visual_suggestion=visual,
            ai_prompt=f"Title direction: {title}. Subtitle direction: {subtitle}. Highlight: {point}.",
        )
        image_plans.append(ImagePlan(
            index=idx, main_title=title, subtitle=subtitle,
            visual_suggestion=visual, ai_prompt=prompt, kit_type=kit_type.value,
        ))

    return ProductPlan(
        refined_selling_points=refined_points,
        image_plans=image_plans,
        mobile_checklist=[
            f"{rule.label}首屏标题不超过8字，副标题不超过15字",
            "手机端预览时主卖点字号优先，辅助说明不压住产品",
            "方图中产品主体占画面60%以上，边缘保留安全留白",
            "浅色背景检查文字对比度，深色背景检查产品轮廓",
        ],
        conversion_checklist=[
            "第一张图直接说明产品和核心利益点",
            "第二张图集中解释最强卖点，避免多个信息抢焦点",
            "场景图要让目标人群和使用场景同时成立",
            "详情或特写图补充材质、做工、功能证据",
            "发布前核对价格、禁用词、平台尺寸和图片清晰度",
        ],
        universal_template={
            "core_goal": f"让{request.target_audience or '目标用户'}快速理解{request.product_name or '产品'}的核心价值并产生购买兴趣",
            "user_understanding": "用户看到后应立即明白：这是什么产品、适合谁、解决什么问题、为什么值得买",
            "main_title": image_plans[0].main_title if image_plans else f"{request.product_name} — {refined_points[0] if refined_points else '品质之选'}",
            "scene_elements": [request.usage_scene or "真实使用场景", request.product_name or "产品主体居中突出", "与场景协调的氛围道具（不抢焦点）", "预留给标题/卖点文字的干净区域"],
            "product_position": "画面主体居中偏下，上方和左侧留白可用于叠加文字",
            "text_white_space": "上方30%区域干净留白，背景不过于复杂",
            "full_prompt": image_plans[0].ai_prompt if image_plans else "",
            "avoid_list": ["不要让产品变形或比例失真", "不要生成错误的品牌Logo或伪文字", "不要卡通化、幻想风格、夸张特效", "不要复杂背景抢产品焦点", "不要出现水印或样机贴图感"],
            "review_checklist": ["产品是否够大够突出？手机端小图能否看清？", "核心卖点是否一眼能读懂？", "是否有干净区域叠加标题/价格文案？", "场景是否真实自然、不像AI生成？", "产品细节有无变形或凭空多出的元素？"],
        },
    )


def create_product_plan_ai(request: PlanRequest) -> ProductPlan:
    """AI-powered plan generation using SiliconFlow GLM-5.2 or DeepSeek."""
    api_key, base_url, default_model = _get_plan_ai_client()
    if not api_key:
        logger.warning("No AI API key configured, falling back to rule mode")
        return _create_product_plan_rule(request)

    user_prompt = _build_ai_user_prompt(request)
    payload = {
        "model": os.environ.get("PLAN_AI_MODEL", default_model),
        "messages": [
            {"role": "system", "content": _AI_PLAN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }

    t0 = time.time()
    req = Request(
        _build_chat_completions_url(base_url),
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=30, context=ssl_context()) as resp:
            data = json.loads(resp.read())
    except URLError as e:
        raise RuntimeError(f"AI API call failed: {e}")

    elapsed = time.time() - t0
    logger.info(f"AI plan generated in {elapsed:.1f}s")

    content_text = data["choices"][0]["message"]["content"]
    ai_result = _parse_ai_response(content_text)

    return _build_product_plan_from_ai(ai_result, request)


def _build_ai_user_prompt(request: PlanRequest) -> str:
    parts = [f"产品名称：{request.product_name or '未指定'}"]
    if request.product_dimensions:
        parts.append(f"尺寸/规格：{request.product_dimensions}")
    if request.product_price:
        parts.append(f"价格：{request.product_price}")
    if request.target_audience:
        parts.append(f"目标用户：{request.target_audience}")
    if request.usage_scene:
        parts.append(f"使用场景：{request.usage_scene}")
    if request.selling_points:
        parts.append(f"卖点：{request.selling_points}")
    if request.competitor_diff:
        parts.append(f"竞品差异：{request.competitor_diff}")
    parts.append(f"平台：{request.platform}")
    parts.append("产品分析上下文（仅供理解产品，不写入 prompt 正文）：")
    parts.append(format_product_image_analysis(request.product_image_analysis))
    selected = selected_plan_kit_types(request)
    parts.append(
        "需要生成的套图类型："
        + "、".join(f"{kit_type.value}（{KIT_LABELS[kit_type]}）" for kit_type in selected)
    )
    parts.append(f"请严格按照以上 {len(selected)} 个套图类型生成方案，image_plans 数量和顺序必须一致。")
    lang = _get_prompt_language(getattr(request, "image_provider", "agnes"))
    parts.append(f"当前图片生成模型类型：{request.image_provider}，prompt语言：{'英文' if lang == 'en' else '中文'}。")
    if not request.selling_points:
        parts.append("用户未提供卖点，请通过产品图分析提炼3-5个核心卖点并用于selling_point和detail类型。")
    else:
        parts.append("用户已提供卖点，请结合产品图分析融合用户卖点生成更有针对性的标注方案。")
    parts.append("detail类型必须包含具体尺寸数值。如果用户未提供尺寸，请根据产品类型估算合理尺寸。")
    parts.append("每个 ai_prompt 只输出第2层场景指令：基于对应模板填空，不改变结构，不写第1层锁定句和第3层收敛句。")
    return "\n".join(parts)


def _parse_ai_response(text: str) -> dict:
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from the text
        match = re.search(r"\{[^{}]*\}(?:\s*[,\n]\s*\{[^{}]*\})*", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise ValueError(f"Failed to parse AI response as JSON: {text[:300]}")


def _build_product_plan_from_ai(ai_result: dict, request: PlanRequest) -> ProductPlan:
    selected = selected_plan_kit_types(request)
    by_type: dict[str, dict] = {}
    for plan_data in ai_result.get("image_plans", []):
        kit_type = plan_data.get("kit_type", "main_white")
        if kit_type not in by_type:
            by_type[kit_type] = plan_data

    fallback = _create_product_plan_rule(request)
    fallback_by_type = {item.kit_type: item for item in fallback.image_plans}

    image_plans: list[ImagePlan] = []
    for index, kit_type in enumerate(selected, start=1):
        plan_data = by_type.get(kit_type.value)
        if plan_data is None:
            fallback_plan = fallback_by_type.get(kit_type.value)
            if fallback_plan is not None:
                image_plans.append(fallback_plan.model_copy(update={"index": index}))
            continue
        image_plans.append(ImagePlan(
            index=index,
            main_title=plan_data.get("main_title", ""),
            subtitle=plan_data.get("subtitle", ""),
            visual_suggestion=plan_data.get("visual_suggestion", ""),
            ai_prompt=fuse_final_plan_prompt(
                request=request,
                kit_type=kit_type,
                title=plan_data.get("main_title", ""),
                subtitle=plan_data.get("subtitle", ""),
                visual_suggestion=plan_data.get("visual_suggestion", ""),
                ai_prompt=plan_data.get("ai_prompt", ""),
            ),
            kit_type=kit_type.value,
        ))

    return ProductPlan(
        refined_selling_points=ai_result.get("refined_selling_points", [])[:5],
        image_plans=image_plans,
        mobile_checklist=ai_result.get("mobile_checklist", []),
        conversion_checklist=ai_result.get("conversion_checklist", []),
    )



def get_available_templates() -> dict:
    return {
        "categories": list(COPY_TEMPLATES.keys()),
        "templates": {
            category: {
                "title_templates": data["title_templates"],
                "subtitle_templates": data["subtitle_templates"],
                "angles": data["angles"],
            }
            for category, data in COPY_TEMPLATES.items()
        },
        "kit_types": [kit.value for kit in PLAN_KIT_SEQUENCE],
    }
