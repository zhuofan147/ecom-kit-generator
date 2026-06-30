"""Template engine: platform rules, kit types, and prompt builders."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class KitType(str, Enum):
    """套图类型 — matches DESIGN.md §1.4"""
    MAIN_WHITE = "main_white"          # 白底主图
    MAIN_SCENE = "main_scene"          # 场景主图
    SELLING_POINT = "selling_point"    # 卖点主图
    SIZE_COMPARE = "size_compare"      # 尺寸对比图
    DETAIL = "detail"                  # 细节特写图
    USAGE_SCENE = "usage_scene"        # 使用场景图
    SKU_VARIANTS = "sku_variants"      # 颜色/款式SKU图
    DETAIL_PAGE = "detail_page"        # 详情页长图
    CAROUSEL = "carousel"              # 首页轮播图
    VIDEO_COVER = "video_cover"        # 视频封面图


KIT_LABELS: dict[KitType, str] = {
    KitType.MAIN_WHITE: "白底主图",
    KitType.MAIN_SCENE: "场景主图",
    KitType.SELLING_POINT: "卖点主图",
    KitType.SIZE_COMPARE: "尺寸对比图",
    KitType.DETAIL: "细节特写图",
    KitType.USAGE_SCENE: "使用场景图",
    KitType.SKU_VARIANTS: "颜色/款式图",
    KitType.DETAIL_PAGE: "详情页长图",
    KitType.CAROUSEL: "轮播图",
    KitType.VIDEO_COVER: "视频封面图",
}

KIT_DESCRIPTIONS: dict[KitType, str] = {
    KitType.MAIN_WHITE: "产品居中，纯白背景，标准电商主图",
    KitType.MAIN_SCENE: "产品融入AI生成的生活/办公场景",
    KitType.SELLING_POINT: "产品 + 核心卖点文案叠加",
    KitType.SIZE_COMPARE: "产品 + 参照物 + 尺寸标注",
    KitType.DETAIL: "材质/局部放大特写",
    KitType.USAGE_SCENE: "产品 + 人物使用场景",
    KitType.SKU_VARIANTS: "多色/多款式并列展示",
    KitType.DETAIL_PAGE: "多段拼接详情长图",
    KitType.CAROUSEL: "首页轮播图",
    KitType.VIDEO_COVER: "视频封面图 16:9",
}

KIT_DIMENSIONS: dict[tuple[str, KitType], tuple[int, int]] = {
    # (platform, kit_type) → (width, height)
    ("taobao", KitType.MAIN_WHITE): (800, 800),
    ("taobao", KitType.MAIN_SCENE): (800, 800),
    ("taobao", KitType.SELLING_POINT): (800, 800),
    ("taobao", KitType.SIZE_COMPARE): (800, 800),
    ("taobao", KitType.DETAIL): (750, 1000),
    ("taobao", KitType.USAGE_SCENE): (800, 800),
    ("taobao", KitType.SKU_VARIANTS): (800, 800),
    ("taobao", KitType.DETAIL_PAGE): (750, 2000),
    ("taobao", KitType.CAROUSEL): (750, 352),
    ("taobao", KitType.VIDEO_COVER): (1280, 720),

    ("jd", KitType.MAIN_WHITE): (800, 800),
    ("jd", KitType.MAIN_SCENE): (800, 800),
    ("jd", KitType.SELLING_POINT): (800, 800),
    ("jd", KitType.DETAIL): (750, 1000),
    ("jd", KitType.USAGE_SCENE): (800, 800),
    ("jd", KitType.SKU_VARIANTS): (800, 800),
    ("jd", KitType.DETAIL_PAGE): (750, 2000),
    ("jd", KitType.CAROUSEL): (750, 352),
    ("jd", KitType.VIDEO_COVER): (1280, 720),

    ("amazon", KitType.MAIN_WHITE): (2000, 2000),
    ("amazon", KitType.MAIN_SCENE): (2000, 2000),
    ("amazon", KitType.SELLING_POINT): (2000, 2000),
    ("amazon", KitType.DETAIL): (1500, 2000),
    ("amazon", KitType.USAGE_SCENE): (2000, 2000),
    ("amazon", KitType.SKU_VARIANTS): (2000, 2000),
    ("amazon", KitType.CAROUSEL): (1920, 600),
    ("amazon", KitType.VIDEO_COVER): (1920, 1080),

    ("offline_store", KitType.MAIN_WHITE): (1080, 1440),
    ("offline_store", KitType.MAIN_SCENE): (1080, 1440),
    ("offline_store", KitType.SELLING_POINT): (1080, 1440),
    ("offline_store", KitType.SIZE_COMPARE): (1080, 1440),
    ("offline_store", KitType.DETAIL): (1080, 1440),
    ("offline_store", KitType.USAGE_SCENE): (1080, 1440),
    ("offline_store", KitType.SKU_VARIANTS): (1080, 1440),
    ("offline_store", KitType.DETAIL_PAGE): (1080, 1920),
    ("offline_store", KitType.CAROUSEL): (1920, 800),
    ("offline_store", KitType.VIDEO_COVER): (1280, 720),
}


@dataclass(frozen=True)
class PlatformRule:
    platform: str
    label: str
    default_width: int
    default_height: int
    background: str  # "white" | "scene" | "any"
    requirement: str
    max_file_size_mb: int = 3
    style_guide: str = ""  # 平台特有风格指引


# ── 通用「不要生成」约束 ── (from 知乎《用 GPT Image-2 做电商图》)
_DONT_CN = (
    "禁止生成：卡通风格、幻想/仙侠风格、夸张的烟雾或光效、过于复杂的背景、"
    "产品变形或比例失真、多余的按钮或接口、非品牌自有的Logo、"
    "无法识别的伪文字、水印、样机贴图感。"
)

_DONT_EN = (
    "DO NOT generate: cartoon style, fantasy/sci-fi style, exaggerated smoke or VFX, "
    "overly complex backgrounds, product deformation or proportion distortion, "
    "extra buttons or ports, non-brand logos, unrecognizable garbled text, "
    "watermarks, mockup collage feel."
)


PLATFORM_RULES: dict[str, PlatformRule] = {
    "taobao": PlatformRule(
        platform="taobao",
        label="淘宝/天猫",
        default_width=800,
        default_height=800,
        background="white",
        requirement="800x800 pure white, product prominently centered, left area reserved for selling point text overlay",
        max_file_size_mb=3,
        style_guide="产品占画面40%以上，左侧留白用于叠加卖点文案，背景极简干净，棚拍级商业摄影。",
    ),
    "jd": PlatformRule(
        platform="jd",
        label="京东",
        default_width=800,
        default_height=800,
        background="white",
        requirement="800x800 pure white, product >80% frame, premium quality",
        max_file_size_mb=3,
        style_guide="产品突出占画面主体，质感高级，纯白背景无干扰，京东高端品质感。",
    ),
    "pdd": PlatformRule(
        platform="pdd",
        label="拼多多",
        default_width=800,
        default_height=800,
        background="white",
        requirement="800x800 product main image, pricing/badge text overlays allowed, strong value perception",
        max_file_size_mb=3,
        style_guide="价格感明显，利益点突出，画面明亮吸引眼球，可叠加促销标签。",
    ),
    "douyin": PlatformRule(
        platform="douyin",
        label="抖音小店",
        default_width=800,
        default_height=800,
        background="white",
        requirement="1:1 main image, lifestyle and scene feel, product clearly visible",
        max_file_size_mb=5,
        style_guide="短视频风格，产品融入真实使用场景，有生活感，不假不摆拍。",
    ),
    "xiaohongshu": PlatformRule(
        platform="xiaohongshu",
        label="小红书",
        default_width=1080,
        default_height=1440,
        background="scene",
        requirement="3:4 vertical, warm natural light, real lifestyle feel, title area reserved at top, not hard-sell",
        max_file_size_mb=5,
        style_guide="温暖自然光，真实生活感，上方留标题区域，不能太像硬广。氛围治愈，有格调。",
    ),
    "amazon": PlatformRule(
        platform="amazon",
        label="Amazon",
        default_width=2000,
        default_height=2000,
        background="white",
        requirement="2000x2000 pure white, product >85% frame area, clean commercial photography",
        max_file_size_mb=10,
        style_guide="Product centered, pure white RGB 255, professional studio lighting, minimal clean look.",
    ),
    "shopify": PlatformRule(
        platform="shopify",
        label="Shopify",
        default_width=2048,
        default_height=2048,
        background="any",
        requirement="2048x2048 or larger, brand-aligned lifestyle photography",
        max_file_size_mb=10,
        style_guide="Brand-first lifestyle, editorial quality, warm tones, aspirational feel.",
    ),
    "ebay": PlatformRule(
        platform="ebay",
        label="eBay",
        default_width=1600,
        default_height=1600,
        background="white",
        requirement="1600x1600, white background recommended, product clearly shown",
        max_file_size_mb=12,
        style_guide="Clean product photography, neutral background, clear product detail.",
    ),
    "offline_store": PlatformRule(
        platform="offline_store",
        label="其他",
        default_width=1080,
        default_height=1440,
        background="scene",
        requirement="1080x1440 offline retail store poster, product hero, store promotion, foot-traffic conversion",
        max_file_size_mb=12,
        style_guide="线下门店产品海报风格，产品作为视觉主角，保留醒目标题、活动信息、价格/优惠和到店引导区域，适合橱窗、展架、门店屏幕展示。",
    ),
}


@dataclass(frozen=True)
class ProductInfo:
    name: str = "产品"
    category: str = ""
    material: str = ""
    audience: str = ""
    selling_points: list[str] = field(default_factory=list)
    brand_tone: str = ""
    usage_scene: str = ""
    dimensions: str = ""


@dataclass(frozen=True)
class KitSpec:
    """Full spec for generating one image in a kit."""
    kit_type: KitType
    platform: str
    width: int
    height: int
    label: str
    prompt: str
    file_suffix: str


def get_platform_rule(platform: str) -> PlatformRule:
    try:
        return PLATFORM_RULES[platform]
    except KeyError as exc:
        raise ValueError(f"Unsupported platform: {platform}") from exc


def product_info_from_dict(data: dict | None) -> ProductInfo:
    data = data or {}
    selling_points = data.get("selling_points") or data.get("sellingPoints") or []
    if isinstance(selling_points, str):
        selling_points = [item.strip() for item in selling_points.split("\n") if item.strip()]
    return ProductInfo(
        name=data.get("name") or "产品",
        category=data.get("category") or "",
        material=data.get("material") or "",
        audience=data.get("audience") or "",
        selling_points=selling_points,
        brand_tone=data.get("brand_tone") or data.get("brandTone") or "",
        usage_scene=data.get("usage_scene") or data.get("usageScene") or "",
        dimensions=data.get("dimensions") or data.get("product_dimensions") or data.get("productDimensions") or "",
    )


def build_prompt(platform: str, kit_type: KitType, product_info: ProductInfo) -> str:
    """Build a generation prompt for a specific platform + kit type.
    
    Language: Chinese for domestic platforms (taobao/jd/pdd/douyin/xiaohongshu),
              English for overseas platforms (amazon/shopify/ebay).
    
    Methodology: 知乎《用 GPT Image-2 做电商图》7要素结构
    ①产品外观 ②使用场景 ③构图位置 ④光线氛围 ⑤文字留白 ⑥画面比例 ⑦不要什么
    """
    rule = get_platform_rule(platform)
    w, h = get_kit_dimensions(platform, kit_type)
    
    is_overseas = platform in ("amazon", "shopify", "ebay")
    
    name = product_info.name or "产品"
    material = product_info.material or ""
    points = product_info.selling_points or []
    scene = product_info.usage_scene or ""
    dimensions = product_info.dimensions or ""
    dimension_text_en = f"Product dimensions/specs: {dimensions}. " if dimensions else ""
    dimension_text_cn = f"产品尺寸/规格：{dimensions}。" if dimensions else ""
    
    # ── Material-specific rendering hints ──
    material_hints_cn = ""
    material_hints_en = ""
    if material:
        mat_lower = material.lower()
        if any(w in mat_lower for w in ["网面", "织物", "mesh", "fabric", "飞织"]):
            material_hints_en = "fabric texture, soft folds, breathable weave visible"
            material_hints_cn = "织物纹理清晰可见，透气网眼细节"
        elif any(w in mat_lower for w in ["皮革", "皮", "leather"]):
            material_hints_en = "leather texture, subtle grain detail, matte finish"
            material_hints_cn = "皮革纹理细腻，哑光质感"
        elif any(w in mat_lower for w in ["橡胶", "rubber", "塑料", "plastic"]):
            material_hints_en = "matte rubber texture, slight specular highlights on edges"
            material_hints_cn = "哑光质感，边缘微弱高光"
        elif any(w in mat_lower for w in ["金属", "metal", "不锈钢"]):
            material_hints_en = "metallic sheen, reflective surface, specular highlights"
            material_hints_cn = "金属光泽，镜面反射高光"
    
    # ── Base prompt with 7要素 structure ──
    if is_overseas:
        base = (
            f"Ecommerce product photo of {name}. "
            f"Appearance: exactly preserve product shape, color, material, proportions from reference. "
            f"Material: {material}. {material_hints_en + '. ' if material_hints_en else ''}"
            f"{dimension_text_en}"
            f"Composition: product centered, {rule.style_guide + '. ' if rule.style_guide else ''}"
            f"Lighting: professional studio soft box, natural looking, no harsh shadows. "
            f"Text space: leave clean area for title/selling point overlay. "
            f"Aspect: {w}x{h}px. "
            f"{_DONT_EN}"
        )
    else:
        base = (
            f"电商产品摄影图，主体：{name}。"
            f"①产品外观：严格保持参考图外形、颜色、材质、比例不变。"
            f"产品材质：{material}。{material_hints_cn + '。' if material_hints_cn else ''}"
            f"{dimension_text_cn}"
            f"②使用场景 + ③构图 + ④光线：{rule.style_guide + '。' if rule.style_guide else ''}"
            f"⑤文字留白：预留干净区域可叠加标题和卖点文案。"
            f"⑥画面比例：{w}x{h}像素。"
            f"⑦{_DONT_CN}"
        )

    # ── Kit-type specific prompts ──
    if is_overseas:
        kit_prompts = _overseas_prompts(kit_type, w, h, name, points, scene, dimensions)
    else:
        kit_prompts = _domestic_prompts(kit_type, w, h, name, points, scene, dimensions)

    return base + " " + kit_prompts


def _overseas_prompts(kt: KitType, w: int, h: int, name: str, points: list, scene: str, dimensions: str = "") -> str:
    """Rich English prompts optimized for Amazon/Shopify/eBay."""
    quoted_features = ", ".join(f'"{point}"' for point in points[:4]) if points else '"key selling points"'
    prompts = {
        KitType.MAIN_WHITE: (
            f"Product centered in frame, pure white background (RGB 255,255,255). "
            f"Product occupies at least 85% of frame area. "
            f"3/4 angle view from slightly above, showing depth and dimension. "
            f"Subtle soft shadow beneath product, rim light along edges for separation. "
            f"No props, no text, no logos — clean minimalist Amazon main image. "
            f"4K resolution, sharp focus across entire product."
        ),
        KitType.MAIN_SCENE: (
            f"Product placed naturally in a {scene or 'modern lifestyle'} setting. "
            f"Warm natural window light, soft ambient shadows, shallow depth of field "
            f"subtly blurring background. Product is the clear focal point. "
            f"Add a few minimal contextual props — wooden floor, a plant, a coffee cup "
            f"— nothing distracting. Magazine editorial quality, aspirational lifestyle feel."
        ),
        KitType.SELLING_POINT: (
            f"Amazon A+ Content style product feature infographic. "
            f"Layout: product prominently on left side (55%), feature text blocks on right (45%). "
            f"Features include: {quoted_features}. "
            f"Use only very short English feature labels or clean blank text placeholders; avoid dense paragraphs. "
            f"Soft gradient background from pearl white to light gray. "
            f"Professional sans-serif typography, clean modern information design. "
            f"Prioritize clean layout so final copy can be overlaid later."
        ),
        KitType.SIZE_COMPARE: (
            f"Product shown next to an iPhone for scale comparison. "
            f"Side-by-side layout on a clean white surface. "
            f"Dimensional arrows with measurements: \"{dimensions or 'both inches and cm'}\". "
            f"Professional infographic style, light gray background, studio lighting."
        ),
        KitType.DETAIL: (
            f"Extreme macro close-up photograph of product material and texture. "
            f"Split composition showing 2-3 detail zones: "
            f"surface texture / stitching quality / sole or bottom detail. "
            f"Shallow depth of field on each zone, studio lighting reveals craftsmanship. "
            f"Clean arrows pointing to each zone with minimal labels such as \"surface texture\", \"stitching quality\", \"sole detail\". Premium quality."
        ),
        KitType.USAGE_SCENE: (
            f"Multi-scene lifestyle collage: 3 usage scenarios side by side in {w}x{h} frame. "
            f"Scene 1 — Commute: person wearing the product on a modern city street, morning light. "
            f"Scene 2 — Leisure: person relaxing in a park, product clearly visible, warm afternoon sun. "
            f"Scene 3 — Shopping: person in a bright mall, casual outfit. "
            f"Each scene labeled with a clean English word overlay: \"Commute\", \"Leisure\", \"Shopping\". "
            f"Top banner: \"Made for Everyday You\" in bold elegant font. "
            f"Magazine lifestyle editorial quality, warm natural tones, product visible in every scene."
        ),
        KitType.SKU_VARIANTS: (
            f"6 color variants of the product in a 2x3 grid on pure white background. "
            f"Variants: White, Black, Gray, Navy, Beige, Olive Green. "
            f"Each cell shows one variant with color name label below: \"White\", \"Black\", \"Gray\", \"Navy\", \"Beige\", \"Olive Green\". "
            f"Consistent 3/4 angle and lighting across all cells. "
            f"Top header: \"Choose Your Style\" in clean sans-serif. "
            f"Professional Amazon catalog style, each variant sharp and clear."
        ),
        KitType.DETAIL_PAGE: (
            f"Long-form Amazon A+ detail page with 4 stacked sections, {w}x{h}px: "
            f"HERO: Full-width product shot with headline \"Light Steps, Confident Every Day\" in bold, "
            f"subheadline \"Thoughtful details for all-day comfort and easy movement\". "
            f"FEATURES: 3-column layout — \"Breathable & Skin-Friendly Upper\" / \"Supportive Heel Design\" / "
            f"\"Non-Slip Durable Outsole\" — each with close-up and 2-line English description. "
            f"MATERIALS: Clean infographic showing material breakdown with labeled callouts. "
            f"SIZE GUIDE: Simple size chart table. "
            f"Plenty of white space, soft color accents, professional typography. "
            f"Every text element must be sharp and legible."
        ),
        KitType.CAROUSEL: (
            f"Wide homepage carousel banner {w}x{h}px. "
            f"Bold composition: product on right side, large English headline on left: "
            f"\"Step Into Comfort\". Subheadline: \"All-day cushioning, everyday style\". "
            f"Vibrant gradient background, dramatic lighting on product. "
            f"Promotional badge in corner. Modern ecommerce hero banner quality."
        ),
        KitType.VIDEO_COVER: (
            f"YouTube thumbnail style, 16:9 {w}x{h}px. "
            f"Product hero shot with dramatic contrast lighting. "
            f"Bold English text: \"UNBOXING & REVIEW\" or \"ON FEET TEST\". "
            f"High-contrast color grade, subtle glow effect. Click-worthy composition."
        ),
    }
    return prompts.get(kt, prompts[KitType.MAIN_WHITE])


def _domestic_prompts(kt: KitType, w: int, h: int, name: str, points: list, scene: str, dimensions: str = "") -> str:
    """Rich Chinese prompts optimized for 淘宝/京东/拼多多/抖音/小红书."""
    quoted_points = "、".join(f'"{point}"' for point in points[:4]) if points else '"核心卖点"'
    prompts = {
        KitType.MAIN_WHITE: (
            f"产品居中构图，纯白背景。产品占画面85%以上面积。"
            f"3/4角度拍摄，展示产品的立体感和进深感。"
            f"底部柔和投影，边缘有微弱轮廓光与背景分离。"
            f"无道具、无文字、无Logo——干净极简的标准白底主图。"
            f"棚拍级商业摄影，画面整体清晰锐利。"
        ),
        KitType.MAIN_SCENE: (
            f"产品自然摆放在{scene or '现代简约生活场景'}中。"
            f"温暖的自然窗光，柔和的氛围阴影，浅景深虚化背景。"
            f"产品是画面的绝对焦点。摆放少量氛围道具——木地板、绿植、咖啡杯"
            f"——以不分散注意力为前提。杂志级编辑摄影，高级生活方式感。"
        ),
        KitType.SELLING_POINT: (
            f"淘宝/天猫详情页风格的产品卖点信息图。"
            f"布局：产品左侧展示（占55%宽度），右侧卖点文案板块（占45%）。"
            f"卖点包括：{quoted_points}。"
            f"每条卖点仅使用图标和极短中文标签，复杂中文长句留白后期叠加，避免生成乱码文字。"
            f"背景从米白到浅灰的柔和渐变，现代简约信息设计。"
            f"专业无衬线字体排版，文字区域保持干净克制。"
        ),
        KitType.SIZE_COMPARE: (
            f"产品与一部iPhone并排对比大小。"
            f"干净的浅色台面，标注尺寸箭头，尺寸标注：\"{dimensions or '厘米和英寸'}\"。"
            f"专业信息图风格，浅灰背景，棚拍布光。"
        ),
        KitType.DETAIL: (
            f"产品材质和工艺的极致微距特写摄影。"
            f"分割画面展示2-3个细节区域：鞋面纹理 / 缝线做工 / 鞋底花纹。"
            f"每个区域浅景深突出质感，棚拍灯光展现做工品质。"
            f"干净箭头指向每个区域带简短标注：\"鞋面纹理\"、\"缝线做工\"、\"鞋底花纹\"。精品品质感。"
        ),
        KitType.USAGE_SCENE: (
            f"三场景生活拼贴图，{w}x{h}像素内并排展示3个使用场景："
            f"场景一「通勤」— 人物穿着产品走在现代都市街道，晨光氛围。"
            f"场景二「休闲」— 人物在公园放松，产品清晰可见，午后暖阳。"
            f"场景三「逛街」— 人物在明亮商场，休闲穿搭。"
            f"每个场景叠加中文标签：\"通勤\"、\"休闲\"、\"逛街\"。顶部标题大字：\"为你的每一天而生\"。"
            f"杂志级生活方式摄影，温暖自然色调，每个场景产品清晰可见。"
        ),
        KitType.SKU_VARIANTS: (
            f"6种颜色款式在纯白背景上以2x3网格排列。"
            f"颜色包括：白色、黑色、灰色、藏青、米色、橄榄绿。"
            f"每格展示一个颜色款，下方标注中文颜色名：\"白色\"、\"黑色\"、\"灰色\"、\"藏青\"、\"米色\"、\"橄榄绿\"。"
            f"所有角度和光线保持一致。顶部标题：\"选择你的风格\"。"
            f"专业天猫/京东级商品目录风格，每款清晰锐利。"
        ),
        KitType.DETAIL_PAGE: (
            f"淘宝/天猫详情页长图，{w}x{h}像素，4个纵向板块堆叠："
            f"板块1「头图」— 全宽产品展示，标题大字\"舒适每一步，自信每一天\"，"
            f"副标题\"全天候舒适体验，从细节开始\"。"
            f"板块2「卖点」— 三栏布局：\"透气亲肤鞋面\" / \"稳固后跟支撑\" / \"防滑耐磨外底\"，"
            f"每栏配局部特写图和一段中文描述。"
            f"板块3「材质」— 信息图风格展示材质分解，带标注箭头指向产品。"
            f"板块4「尺码」— 简洁的尺码对照表。"
            f"大量留白，柔和色彩点缀，专业排版，所有文字清晰锐利。"
        ),
        KitType.CAROUSEL: (
            f"首页轮播横幅 {w}x{h}像素。"
            f"大胆构图：产品居中偏右，左侧大字中文标题\"踏出舒适每一步\"。"
            f"副标题\"全天候缓震，每日型搭\"。"
            f"渐变品牌色背景，产品戏剧化布光。角落促销标签。"
            f"现代电商首页横幅品质。"
        ),
        KitType.VIDEO_COVER: (
            f"视频封面图 16:9比例 {w}x{h}像素。"
            f"产品特写带强对比布光。"
            f"大字中文标题：\"开箱实测\"或\"上脚体验\"。"
            f"高对比度调色，微妙辉光效果。点击欲强的封面构图。"
        ),
    }
    return prompts.get(kt, prompts[KitType.MAIN_WHITE])


def get_kit_dimensions(platform: str, kit_type: KitType) -> tuple[int, int]:
    """Get output dimensions for a platform + kit type combo."""
    key = (platform, kit_type)
    if key in KIT_DIMENSIONS:
        return KIT_DIMENSIONS[key]
    rule = get_platform_rule(platform)
    return rule.default_width, rule.default_height


def build_review_prompt(platform: str, kit_type: KitType, product_info: ProductInfo) -> str:
    """Build a post-generation review prompt (文章 §07: 出图后让 Codex 检查).
    
    Checks 5 dimensions from ecommerce conversion perspective.
    """
    is_overseas = platform in ("amazon", "shopify", "ebay")
    name = product_info.name or "产品"
    points = "、".join(product_info.selling_points) if product_info.selling_points else "核心卖点"
    kt_label = KIT_LABELS.get(kit_type, kit_type.value)
    
    if is_overseas:
        return (
            f"Review this {kt_label} image for {name} from an ecommerce conversion perspective. "
            f"Check: 1) Is the product prominent enough (size in frame)? "
            f"2) Are the selling points ({points}) clearly visible? "
            f"3) Is there clean space for title/text overlay? "
            f"4) Can a mobile user understand it at thumbnail size? "
            f"5) Does the scene look realistic, not AI-generated? "
            f"6) Any product deformation, wrong details, or hallucinated elements? "
            f"7) Does the lighting and color match a professional product photo? "
            f"Give specific fix suggestions, not generic comments."
        )
    else:
        return (
            f"从电商转化角度检查这张{name}的{kt_label}。"
            f"重点看：1）产品是否够大够突出？"
            f"2）卖点（{points}）有没有表达清楚？"
            f"3）有没有预留文字/标题位置？"
            f"4）手机端小图能不能看懂？"
            f"5）场景是否真实、会不会太像AI生成？"
            f"6）产品有没有变形、细节错误或凭空多出东西？"
            f"7）光线和色彩是否符合专业产品摄影？"
            f"请给出具体的修改建议，不要泛泛而谈。"
        )


def build_kit_specs(
    platform: str,
    kit_types: list[KitType],
    product_info: ProductInfo,
    size_overrides: dict[KitType, tuple[int, int]] | None = None,
) -> list[KitSpec]:
    """Build full generation specs for all requested kit types."""
    size_overrides = size_overrides or {}
    specs: list[KitSpec] = []
    for kt in kit_types:
        w, h = size_overrides.get(kt, get_kit_dimensions(platform, kt))
        specs.append(KitSpec(
            kit_type=kt,
            platform=platform,
            width=w,
            height=h,
            label=KIT_LABELS.get(kt, kt.value),
            prompt=build_prompt(platform, kt, product_info).replace(
                f"{get_kit_dimensions(platform, kt)[0]}x{get_kit_dimensions(platform, kt)[1]}",
                f"{w}x{h}",
            ),
            file_suffix=kt.value,
        ))
    return specs
