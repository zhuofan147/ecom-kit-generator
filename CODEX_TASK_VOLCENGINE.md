# Task: 接入火山方舟 Seedream 5.0 图生图 Provider

## 背景
ecom-kit-generator 项目需要接入火山方舟（Volcengine Ark）的 Seedream 5.0 模型作为图片生成 provider。这是真正的 img2img 模型，能基于参考图生成产品图，解决现有 provider（agnes/siliconflow）不识别参考图的问题。

## API Key
```
ark-d438adc3-d526-450f-9a36-65d5dc38f22a-b18b3
```

## 官方 API 文档（curl 示例）
```bash
curl -X POST https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ark-d438adc3-d526-450f-9a36-65d5dc38f22a-b18b3" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "生成狗狗趴在草地上的近景画面",
    "image": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imageToimage.png",
    "sequential_image_generation": "disabled",
    "response_format": "url",
    "size": "2K",
    "stream": false,
    "watermark": true
}'
```

## 你要做的事

### 1. 先测试 API 连通性
用上面的 curl 示例（换成你的 prompt）测试文生图和图生图，确认 key 能用。
注意：`image` 参数官方示例传的是 URL，你需要测试是否也支持 base64 data URL（因为我们的产品图存在本地）。如果不支持 base64，就需要先把图片上传到某个可公网访问的地方再传 URL。

### 2. 新增 VolcEngineArkProvider 类
在 `backend/app/services/imagegen.py` 中新增 `VolcEngineArkProvider` 类，实现 `ImageGenerationProvider` 接口：

- `__init__`: 读取 API key（从环境变量 `VOLCENGINE_ARK_API_KEY` 或直接硬编码）
- `generate_image`: 
  - 读取产品参考图，转 base64 data URL 或上传获取 URL
  - 构建 prompt（用现有的 request.prompt）
  - 调用 `https://ark.cn-beijing.volces.com/api/v3/images/generations`
  - model: `doubao-seedream-5-0-260128`
  - 传 `image` 参数做图生图
  - `sequential_image_generation`: "disabled"
  - `response_format`: "url"
  - `size`: 根据请求的 width/height 选择最接近的预设值（支持 "1K"、"2K" 等，查文档确认支持的 size 值）
  - `stream`: false
  - `watermark`: false
  - 下载返回的图片 URL 保存到 request.output_path

### 3. 注册 Provider
在 `backend/app/config/providers.py` 的 `PROVIDER_REGISTRY` 中添加：
```python
ProviderMeta(
    name="volcengine-ark",
    label="火山方舟 Seedream 5.0",
    description="火山方舟豆包 Seedream 5.0，真图生图，产品一致性最佳",
    env_vars=["VOLCENGINE_ARK_API_KEY"],
),
```

### 4. 在 create_provider() 工厂函数中注册
在 `imagegen.py` 的 `create_provider()` 函数中添加：
```python
elif name == "volcengine-ark":
    return VolcEngineArkProvider()
```

### 5. 把 API Key 写入 .env
在项目根目录 `.env` 文件中添加：
```
VOLCENGINE_ARK_API_KEY=ark-d438adc3-d526-450f-9a36-65d5dc38f22a-b18b3
```

### 6. 测试出图
- 重启后端
- 用产品图 `backend/outputs/uploads/da8f80ac78074faa8ed05f3f5d0ded34/original.jpg`（粉色运动鞋）测试白底主图
- v3 prompt: `Use the exact product from the reference image. Maintain product consistency including material, color, and shape. The product centered, occupying 70-80% of frame. Pure white background RGB(255,255,255). Professional studio lighting: top softbox + dual side fill lights, even and soft, no hard shadows. Natural soft shadow beneath product. Front view, eye-level. Commercial product photography style. Photorealistic product photography, 8k, e-commerce quality, sharp and clean.`
- 确认生成的图片是一双粉色运动鞋（不是电子产品！）

### 测试用产品图路径
`/Users/zs-hk/projects/ecom-kit-generator/backend/outputs/uploads/da8f80ac78074faa8ed05f3f5d0ded34/original.jpg`
这是一只粉色运动鞋放在草地上的照片。

### 验收标准
1. API 连通，文生图和图生图都能出图
2. 图生图模式下，粉色运动鞋保持为鞋，不变成其他产品
3. 白底主图背景为纯白
4. Provider 注册完成，前端能选择"火山方舟 Seedream 5.0"
5. 通过后端 API `POST /api/generate/kit` 用 `provider: "volcengine-ark"` 能成功出图
6. 生成图片保存到 `backend/outputs/generated/` 目录

## 重要
- 不要改 plan_engine.py，v3 prompt 框架已经定稿
- 只改 imagegen.py、providers.py、.env
- 代码风格跟现有 provider 保持一致
- 如果 image 参数不支持 base64，想替代方案（比如先上传到火山 TOS、或用后端的 localhost URL 但注意火山服务器访问不了 localhost）
