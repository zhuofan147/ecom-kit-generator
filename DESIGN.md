# 电商/广告AI套图生成工具 · 设计方案

## 产品定位

一键上传产品图 → AI 自动生成多平台电商套图 + 广告宣传物料。支持国内电商/跨境电商不同规则，支持选填产品信息优化生图质量，支持遮罩编辑和提示词微调单张图。

---

## 1. 核心功能

### 1.1 上传与预处理
- 拖拽/点击上传产品图（支持 JPG/PNG/WebP，最大 20MB）
- AI 自动抠图（rembg / RMBG-2.0），分离产品主体与背景
- 手动微调控件：画笔修复抠图边缘、橡皮擦
- 产品图多角度支持（可上传正面/侧面/45°多张图）

### 1.2 产品信息选填（优化生图质量）
| 字段 | 类型 | 用途 |
|------|------|------|
| 产品名称 | 文本 | 生图提示词中描述产品 |
| 产品类目 | 下拉 | 匹配行业模板（服装/3C/美妆/食品/家居…） |
| 材质/颜色 | 标签 | 产品质感描述 |
| 受众群体 | 多选 | 调整场景风格（年轻女性/商务人士/母婴…） |
| 核心卖点 | 文本(≤3条) | 生成文案叠加到详情图 |
| 品牌调性 | 选择 | 简约/科技感/国潮/北欧/奢华… |
| 使用场景 | 多选 | 办公/户外/居家/聚会… → AI 生成对应背景 |
| 参考风格图 | 上传 | AI 提取风格迁移 |

### 1.3 平台规则预设

#### 国内电商
| 平台 | 主图 | 详情图 | 首页图 | 特殊要求 |
|------|------|------|------|------|
| 淘宝/天猫 | 800×800, 白底 | 750×不限, ≤3MB | 可带文案 | 第5张须白底 |
| 京东 | 800×800, 白底 | 750×不限 | 无严格限制 | 主图须纯白底 |
| 拼多多 | 800×800 | 750×不限 | 轮播图750×352 | 主图可带文案 |
| 抖音小店 | 1:1, 白底 | 3:4 竖版 | 3:4 竖版 | 强调场景感 |
| 小红书 | 3:4 竖版 | 3:4 竖版 | 1:1 | 主图文案≤20字 |

#### 跨境电商
| 平台 | 主图 | 详情图 | A+内容 | 特殊要求 |
|------|------|------|------|------|
| Amazon | 2000×2000, 纯白底 | 无限制 | 970×600 (A+) | 主图占画面≥85% |
| Shopify | 2048×2048 | 无限制 | — | 自定义 |
| eBay | 1600×1600 | 无限制 | — | 白底推荐 |
| Shopee | 800×800 | 无限制 | — | 同淘宝 |

### 1.4 套图生成类型

#### 电商套图（一键勾选）
- [x] 白底主图（自动适配平台尺寸）
- [x] 场景主图（产品+AI生成场景）
- [x] 卖点主图（产品+卖点文字叠加）
- [x] 尺寸对比图（产品+参照物）
- [x] 细节特写图（材质/局部放大）
- [x] 使用场景图（产品+AI人物/场景）
- [x] 颜色/款式SKU图（多色展示）
- [x] 详情页长图（多段拼接）
- [x] 首页轮播图
- [x] 视频封面图

#### 广告套图（一键勾选 + 自定义添加）
- [x] 海报（A4竖版/A3横版）
- [x] 宣传单/折页（A4三折）
- [x] 立牌/易拉宝（80×200cm）
- [x] 桌面展架（A5/A4）
- [x] 门头横幅
- [x] 社交媒体方图（1:1）
- [x] 朋友圈海报（9:16）
- [x] 公众号封面（900×383）
- [x] 优惠券/促销卡
- [x] 自定义尺寸（手动输入宽高）

### 1.5 生成后编辑
- **提示词微调**：选中某张已生成的图 → 输入补充提示词 → 局部重新生成
- **遮罩编辑**：在图上涂抹遮罩区域 → 输入修改描述 → AI 仅修改遮罩区域（类似 Photoshop 生成式填充）
- **文字叠加**：添加/修改产品名、卖点、价格等
- **布局调整**：拖拽产品位置、缩放
- **批量导出**：选中多张 → 一键下载 ZIP / 导出到本地

---

## 2. 技术架构

```
┌──────────────────────────────────────────────┐
│              Frontend (Next.js)               │
│  ┌─────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Upload  │ │ Editor   │ │ Template      │  │
│  │ Canvas  │ │ Mask UI  │ │ Selector      │  │
│  └────┬────┘ └────┬─────┘ └───────┬───────┘  │
│       │           │               │          │
│  ┌────┴───────────┴───────────────┴───────┐  │
│  │        State Manager (Zustand)          │  │
│  └────────────────┬───────────────────────┘  │
└───────────────────┼──────────────────────────┘
                    │ REST API + WebSocket
┌───────────────────┼──────────────────────────┐
│              Backend (FastAPI)                │
│  ┌──────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ rembg    │ │ Codex   │ │ Canvas        │  │
│  │ 抠图服务 │ │ API桥接 │ │ Render 渲染   │  │
│  └──────────┘ └────┬────┘ └──────────────┘  │
│                    │                         │
│  ┌─────────────────┴──────────────────────┐  │
│  │  Template Engine (平台规则 + 模板)      │  │
│  │  - size_rules.yaml (尺寸/白底/文案规则) │  │
│  │  - templates/ (场景模板+布局模板)       │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  Job Queue (SQLite + asyncio)           │  │
│  │  批量生成、进度推送(WebSocket)           │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### 技术栈
- **前端**：Next.js 14 + TypeScript + TailwindCSS + Fabric.js (Canvas 编辑) + Zustand
- **后端**：FastAPI + Python 3.11 + rembg + Pillow
- **AI 生图**：通过 Codex CLI imagegen（内置）/ 或 fal.ai API / 或 ComfyUI
- **实时通信**：WebSocket（生成进度推送）
- **数据库**：SQLite（任务记录 + 模板存储）
- **文件存储**：本地 `outputs/` 目录

---

## 3. 核心流程

### 生图流程
```
用户上传产品图
  → rembg 抠图 → 产品主体 mask
  → 用户选平台 + 勾选套图类型 + 填写产品信息
  → Template Engine 生成每张图的 prompt + 布局参数
  → 批量 Queue → Codex imagegen 逐张生成
  → WebSocket 推送进度
  → 图生成了 → 渲染到画布 → 叠加文字/卖点
  → 用户审核 → 微调/遮罩编辑 → 重新生成
  → 导出
```

### 每张图的 Prompt 构造（六段式）
```
[产品描述+卖点] + [场景定位] + [视角/构图] + [光影/色调] + [材质质感] + [平台要求]
```

### 示例 Prompt（Amazon 主图）
```
A sleek wireless Bluetooth earphone in matte black, centered in frame,
floating on pure white background, top-down view, studio lighting,
soft shadows beneath, polished plastic texture, product photography,
commercial clean style, 2000x2000px, product occupies >85% frame area
```

---

## 4. 文件结构

```
~/projects/ecom-kit-generator/
├── DESIGN.md
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # 主页面
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── UploadZone.tsx       # 上传区（拖拽/点击）
│   │   │   ├── ProductInfoForm.tsx  # 产品信息表单（选填）
│   │   │   ├── PlatformSelector.tsx # 平台选择（国内/跨境）
│   │   │   ├── KitTypeSelector.tsx  # 套图类型勾选（电商+广告）
│   │   │   ├── TemplatePreview.tsx  # 模板预览网格
│   │   │   ├── ImageCanvas.tsx      # 单图编辑画布（Fabric.js）
│   │   │   ├── MaskEditor.tsx       # 遮罩编辑器
│   │   │   ├── PromptEditor.tsx     # 提示词微调面板
│   │   │   ├── ExportPanel.tsx      # 导出面板
│   │   │   └── ProgressBar.tsx      # 生成进度
│   │   ├── store/
│   │   │   └── index.ts            # Zustand 全局状态
│   │   ├── lib/
│   │   │   ├── api.ts              # 后端 API 封装
│   │   │   ├── platform-rules.ts   # 平台规则定义
│   │   │   └── prompt-builder.ts   # Prompt 构造器
│   │   └── types/
│   │       └── index.ts
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── routers/
│   │   │   ├── upload.py           # 上传+抠图
│   │   │   ├── generate.py         # 生成套图
│   │   │   ├── edit.py             # 遮罩编辑+提示词微调
│   │   │   └── export.py           # 导出
│   │   ├── services/
│   │   │   ├── rembg_service.py    # 抠图服务
│   │   │   ├── imagegen_service.py # Codex imagegen 桥接
│   │   │   ├── template_engine.py  # 模板引擎
│   │   │   └── mask_service.py     # 遮罩处理
│   │   ├── models/
│   │   │   ├── job.py              # 任务模型
│   │   │   └── template.py         # 模板模型
│   │   └── config/
│   │       ├── platforms.yaml      # 平台规则配置
│   │       └── templates.yaml      # 模板定义
│   └── outputs/                    # 生成图片输出目录
└── data/
    └── ecom-kit.db                  # SQLite 数据库
```

---

## 5. API 设计

### 5.1 上传 + 抠图
```
POST /api/upload
  → multipart/form-data, file: image
  ← { product_id, original_url, masked_url, mask_data }

POST /api/upload/multi
  → 多角度上传
  ← [{ product_id, angle, urls }]
```

### 5.2 生成套图
```
POST /api/generate/kit
  Body: {
    product_id: str,
    platform: "taobao" | "amazon" | ...,
    kit_types: ["main_white", "main_scene", "detail", ...],
    product_info: {
      name, category, material, audience, selling_points, brand_tone, usage_scene
    },
    reference_style_image: url?,
    count_per_type: int = 2
  }
  ← { job_id, total_images, websocket_url }

WS /ws/job/{job_id}
  → { type: "progress", current: 3, total: 10, image_url: "..." }
  → { type: "complete", images: [...], job_id }
```

### 5.3 编辑
```
POST /api/edit/rephrase
  Body: { image_id, prompt_supplement: "add golden rim light" }
  ← { new_image_url }

POST /api/edit/mask
  Body: { image_id, mask_data: base64, edit_prompt: "replace with marble table" }
  ← { new_image_url }

POST /api/edit/text
  Body: { image_id, text_overlays: [{content, x, y, font, color, size}] }
  ← { new_image_url }
```

### 5.4 导出
```
POST /api/export
  Body: { image_ids: [...], format: "zip" | "individual" }
  ← { download_url }
```

---

## 6. 开发阶段

### Phase 1：基础骨架（先跑通上传→抠图→生图链路）
- Next.js 项目搭建 + Tailwind
- FastAPI 项目搭建
- 上传组件 + rembg 抠图
- Codex imagegen 桥接验证
- 最简单的「上传→白底图」链路打通

### Phase 2：平台规则 + 模板系统
- platforms.yaml 配置
- Template Engine 实现
- 套图类型选择 UI
- 产品信息表单
- 多图并行生成 + 进度推送

### Phase 3：编辑功能
- ImageCanvas 画布组件
- 遮罩编辑
- 提示词微调
- 文字叠加

### Phase 4：广告套图
- 广告物料模板（海报/宣传单/立牌…）
- 自定义尺寸
- 批量导出

### Phase 5：体验优化
- 拖拽排序
- 历史记录
- 模板收藏/自定义模板
- 跨境电商多语言文案

---

## 7. 参考竞品

| 产品 | 核心功能 | 可借鉴 |
|------|------|------|
| 摄图AI (shetu.ai) | 上传→AI场景→套图 | 场景模板丰富度 |
| 美图设计室 | 模板+AI生图 | 广告物料模板 |
| PhotoRoom | 抠图+背景替换 | API设计+遮罩编辑 |
| 稿定AI | AI电商设计 | 平台规则适配 |
| Canva AI | 模板+AI生图 | 品牌调性系统 |

---
*Generated by Hermes for Codex implementation.*
