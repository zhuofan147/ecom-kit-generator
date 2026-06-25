# Task: 更新 plan_engine.py 提示词工程为 v3 三层框架

## 背景
项目 `backend/app/services/plan_engine.py` 当前的 prompt 工程存在严重问题，需要按 v3 三层框架重构。

## 要改的文件
- `backend/app/services/plan_engine.py` — 核心改动
- `backend/app/services/product_image_analysis.py` — 产品分析不再注入 prompt

## v3 框架核心

最终 prompt = `[系统]第1层锁定句 + [AI]第2层场景指令(基于模板填空) + [系统]第3层收敛句`

### 第1层：产品锁定（系统固定，所有套图通用）

英文: `"Use the exact product from the reference image. Maintain product consistency including material, color, and shape."`

### 第2层：AI 基于模板框架生成（不是自由发挥）

定义 6 个模板常量，AI 负责把 `[占位符]` 替换为具体内容：

```python
TEMPLATE_WHITE_BG = """[PRODUCT] centered, occupying 70-80% of frame. Pure white background RGB(255,255,255). Professional studio lighting: top softbox + dual side fill lights, even and soft, no hard shadows. Natural soft shadow beneath product. Front view, eye-level. Commercial product photography style."""

TEMPLATE_SELLING_POINT = """[PRODUCT] centered. [GRADIENT_COLOR] gradient background. Annotation arrows pointing to: [SELLING_POINT_1], [SELLING_POINT_2], [SELLING_POINT_3]. Callout boxes with clean text layout, whitespace around each annotation. 45-degree side lighting, natural shadow. High-end commercial feel."""

TEMPLATE_SCENE = """[PRODUCT] placed in [SCENE_DESC]. Surrounding props: [PROPS] to build atmosphere. Product remains visual center. Scene title "[TITLE]" at top-left. 85mm f/1.4, shallow depth of field, warm natural lighting."""

TEMPLATE_DETAIL = """Zoom-in on [DETAIL_AREA_1] and [DETAIL_AREA_2] of [PRODUCT]. 10x magnification. Highlight [CRAFTSMANSHIP: stitching/texture/material transition]. Soft side lighting to reveal texture. Material label "[MATERIAL_LABEL]". Pure white background."""

TEMPLATE_SIZE_COMPARE = """[PRODUCT] beside [REFERENCE_OBJECT: iPhone 15 Pro / A4 paper / adult hand] for scale. Bottom-aligned. Dimension annotations: "[DIMENSIONS]". Pure white background, top-down view, even lighting. Product edges sharp, proportions accurate."""

TEMPLATE_USE_SCENE = """Person [ACTION] [PRODUCT] in [SCENE_DESC]. Natural hand-to-product contact. Scene caption "[CAPTION]" at bottom. Candid photography style, 35mm lens, natural lighting."""
```

### 第3层：收敛句（系统固定）

英文: `"Photorealistic product photography, 8k, e-commerce quality, sharp and clean."`

## 具体改动点

### 1. 删除旧的 `build_kit_type_prompt()` 硬编码 body

旧代码里每种套图类型的 body 是硬编码的（比如白底主图有 `no props, no marketing text`），全部删掉。

### 2. 新增 `build_layer1()` 函数

```python
def build_layer1() -> str:
    return "Use the exact product from the reference image. Maintain product consistency including material, color, and shape."
```

### 3. 新增 `build_layer3()` 函数

```python
def build_layer3() -> str:
    return "Photorealistic product photography, 8k, e-commerce quality, sharp and clean."
```

### 4. 新增 `get_template(kit_type)` 函数

根据 kit_type 返回对应的模板常量。映射关系：
- `white_bg` / `白底主图` → TEMPLATE_WHITE_BG
- `selling_point` / `卖点主图` → TEMPLATE_SELLING_POINT
- `scene` / `场景主图` → TEMPLATE_SCENE
- `detail` / `细节特写` → TEMPLATE_DETAIL
- `size_compare` / `尺寸对比` → TEMPLATE_SIZE_COMPARE
- `use_scene` / `使用场景` → TEMPLATE_USE_SCENE

### 5. 改造 `_AI_PLAN_SYSTEM_PROMPT`

AI 的角色从"写完整 prompt"改为"只写第2层：基于模板填空"：

```
你的任务：根据模板框架 + 产品信息 + 用户输入，生成每种套图类型的第2层场景指令。

工作方式：
1. 读取下方的模板框架，理解每种套图类型的结构
2. 读取产品分析信息（颜色/材质/品类/尺寸）— 仅用于理解产品，不写入 prompt
3. 读取用户输入（卖点/场景偏好/尺寸数据）— 有则用，无则根据产品分析提炼
4. 将模板中的 [占位符] 替换为具体内容，可增加细节但不改变结构
5. 布光/相机参数/占比等技术参数保持模板原样

禁止：
- 描述产品外观（颜色/材质/形状）→ 靠参考图
- 使用否定词（no/don't/without）
- 写画质标签（8k/masterpiece）→ 系统第3层统一加
- 改变模板结构
```

### 6. 改造 `fuse_final_plan_prompt()`

旧逻辑：`prefix + body + ai_prompt当尾巴追加`
新逻辑：`layer1 + ai_generated_layer2 + layer3`

```python
def fuse_final_plan_prompt(kit_type: str, ai_generated_scene: str) -> str:
    layer1 = build_layer1()
    layer3 = build_layer3()
    return f"{layer1} {ai_generated_scene} {layer3}"
```

### 7. 改造 `product_image_analysis.py`

`format_product_image_analysis()` 的输出不再注入到 prompt 正文。它只作为 AI system prompt 的上下文信息，让 AI 理解产品。

### 8. 删除旧的 prefix 中的内容

旧的 prefix 包含：
- `img2img task: Generate [套图] based on the uploaded product image` → 删
- 产品分析的颜色/尺寸描述 → 删
- `Maintain identical outline, proportions, color, logo, openings, ports, transparent areas, material texture, surface highlights and edge details` → 删（枚举太多 = 描述外观）
- `no props, no marketing text` → 删（否定词）

## 验收标准

1. 最终 prompt 是三层拼接：layer1 + AI生成的layer2 + layer3
2. 产品分析信息不出现在 prompt 正文中
3. 没有 `no props` / `no text` 等否定词
4. 没有 `Generate...based on...` 重新生成语气
5. 锁定句只说材质/颜色/形状，不枚举孔位/接口/Logo
6. 收敛句包含 `8k`
7. AI 的 system prompt 明确要求"基于模板填空，不改变结构"
8. 6个套图类型模板都有定义且可被 get_template() 返回

## 注意
- 保持现有函数签名兼容，不要改 API 路由
- 保持 `plan_engine.py` 中其他不相关的函数不变
- 代码风格和现有的保持一致
