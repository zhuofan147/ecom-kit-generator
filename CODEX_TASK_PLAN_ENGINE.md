# Codex Task: 电商套图方案规划引擎 (Plan Engine)

## 目标
在现有 `ecom-kit-generator` 项目中新增「方案规划」层，实现：输入产品信息 → AI 分析 → 输出结构化套图方案 → 驱动批量生成。

## 背景
当前项目（`~/projects/ecom-kit-generator/`）已有：
- **Backend**（FastAPI + .venv）: 上传→rembg 抠图→Mock 生图（10 种套图类型）
- **Frontend**（Next.js 14）: PlatformSelector + KitTypeSelector + 批量生成
- **核心文件**: `backend/app/services/template_engine.py`（平台规则+套图类型）、`backend/app/services/imagegen.py`（Mock provider）

## 需要新增的功能

### 1. 方案规划引擎 (Backend)
新建 `backend/app/services/plan_engine.py`：

```python
# 输入
class PlanRequest:
    product_name: str        # 产品名称
    product_price: str       # 价格
    target_audience: str     # 目标人群
    usage_scene: str         # 使用场景
    selling_points: str      # 核心卖点（自由文本）
    competitor_diff: str     # 竞品差异
    platform: str            # 平台

# 输出
class ProductPlan:
    refined_selling_points: list[str]    # AI 提炼的 5 个核心卖点
    image_plans: list[ImagePlan]         # 5 张主图规划
    mobile_checklist: list[str]          # 手机端可读性检查
    conversion_checklist: list[str]      # 发布前转换检查清单

class ImagePlan:
    index: int                  # 第几张
    main_title: str             # 主标题（≤8字）
    subtitle: str               # 副标题（≤15字）
    visual_suggestion: str      # 画面建议（给设计师看）
    ai_prompt: str              # AI 生图提示词（六段式）
    kit_type: str               # 对应套图类型
```

**规则引擎实现**（No LLM required — 用规则+模板生成，Mock 阶段）：
- 根据 `platform` 匹配平台规则（已有 `template_engine.py`）
- 根据产品类目/卖点/人群生成不同的标题文案模板
- 卖点提炼：解析输入的 selling_points，按"功能/体验/性价比/外观/场景"分类
- 画面建议：根据类目+场景匹配预设的构图/色调模板
- AI prompt：用六段式 prompt 模板拼接（已有 `build_prompt`）

### 2. API 端点
在 `backend/app/routers/` 新建 `plan.py`：

```
POST /api/plan
  Body: PlanRequest
  Response: ProductPlan

GET /api/plan/templates  → 返回可用模板列表
```

### 3. 前端集成
- 在 `page.tsx` 左侧面板新增「方案规划」步骤
- 新增 `PlanView` 组件：展示提炼后的卖点 + 主图规划卡片
- 点击"确认方案并生成套图"→ 将 ImagePlan 的 ai_prompt 传给现有生成管线

### 4. 文案模板库
新建 `backend/app/config/copy_templates.py`：
- 按类目（3C/服装/美妆/食品/家居）分类
- 每种包含：标题模板、副标题模板、卖点角度
- 支持 {product_name} {price} {audience} 等变量替换

## 约束
- 不引入真实 LLM 调用（Mock 阶段用规则引擎）
- 保持现有 10 种套图类型的 Mock 生图逻辑不动
- 前端用现有组件风格（Tailwind + lucide-react）
- 后端用 .venv Python（`backend/.venv/bin/python3`）
- 所有新增文件放对位置，不破坏现有结构

## 验收标准
1. `POST /api/plan` 输入产品信息 → 返回完整 ProductPlan（5 卖点 + 5 图规划 + 检查清单）
2. 前端可看到结构化方案卡片，点击即可触发现有批量生成
3. 生成的套图 prompt 比之前的更丰富（含标题、画面建议、六段式 prompt）
4. 前端编译通过 + 后端启动无报错
