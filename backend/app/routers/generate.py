"""Generation API: create jobs for multi-kit image generation."""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import GENERATED_DIR, OUTPUT_DIR, RETOUCHED_DIR
from app.routers.upload import resolve_masked_upload, resolve_reference_uploads
from app.services.imagegen import ImageGenerationRequest, create_provider
from app.services.jobs import JobStore
from app.services.plan_engine import PlanRequest, create_product_plan
from app.services.product_image_analysis import analyze_product_cutout
from app.services.template_engine import KitType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["generate"])
job_store = JobStore(output_dir=GENERATED_DIR)

# Default kit types for full ecommerce image set
DEFAULT_KIT_TYPES = [
    "main_white", "selling_point", "main_scene", "detail", "usage_scene",
]


class GenerateRequest(BaseModel):
    product_id: str
    platform: str = "taobao"
    product_info: dict = Field(default_factory=dict)
    kit_types: list[str] = Field(default_factory=lambda: DEFAULT_KIT_TYPES[:])
    kit_sizes: dict[str, dict[str, int]] = Field(default_factory=dict)
    provider: str = "agnes"
    run_plan: bool = True  # Auto-run plan engine before generating
    llm_config: dict = Field(default_factory=dict)  # 前端设置栏配的 LLM API
    image_config: dict = Field(default_factory=dict)  # 前端设置栏配的生图 API
    vision_config: dict = Field(default_factory=dict)  # 前端设置栏配的识图 API


@router.post("/generate/kit")
async def create_generation_job(request: GenerateRequest):
    try:
        masked_path = resolve_masked_upload(request.product_id)
        reference_paths = resolve_reference_uploads(request.product_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="找不到已上传的产品图")

    product_info = dict(request.product_info)
    size_overrides: dict[KitType, tuple[int, int]] = {}
    for raw_kit_type, raw_size in request.kit_sizes.items():
        try:
            kit_type = KitType(raw_kit_type)
        except ValueError:
            continue
        width = raw_size.get("w")
        height = raw_size.get("h")
        if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
            size_overrides[kit_type] = (width, height)

    # Auto-run plan engine to generate AI prompts
    if request.run_plan:
        try:
            plan_request = PlanRequest(
                product_name=product_info.get("name", ""),
                product_dimensions=product_info.get("dimensions", ""),
                product_price=product_info.get("price", ""),
                target_audience=product_info.get("audience", ""),
                usage_scene=product_info.get("usage_scene", ""),
                selling_points=product_info.get("selling_points", ""),
                competitor_diff=product_info.get("competitor_diff", ""),
                platform=request.platform,
                kit_types=request.kit_types,
                kit_sizes=request.kit_sizes,
                product_image_analysis=analyze_product_cutout(
                    masked_path,
                    llm_api_url=request.vision_config.get("apiUrl") or os.environ.get("VISION_BASE_URL", "https://api.scnet.cn/api/llm/v1"),
                    llm_api_key=request.vision_config.get("apiKey") or os.environ.get("VISION_API_KEY", ""),
                    llm_model=request.vision_config.get("model") or os.environ.get("VISION_MODEL", "Qwen3.6-Plus"),
                ),
                image_provider=request.provider,
                llm_config=request.llm_config,
                vision_config=request.vision_config,
            )
            plan = create_product_plan(plan_request)
            # Store AI prompts keyed by kit_type
            product_info["planned_prompts"] = {
                ip.kit_type: ip.ai_prompt for ip in plan.image_plans
            }
            product_info["plan_data"] = plan.model_dump()
            product_info["refined_selling_points"] = plan.refined_selling_points
            logger.info(f"Plan generated: {len(plan.image_plans)} image plans")
        except Exception as e:
            logger.warning(f"Plan generation failed, using raw prompts: {e}")

    job = job_store.create_generation_job(
        product_id=request.product_id,
        masked_path=masked_path,
        platform=request.platform,
        product_info=product_info,
        kit_types=request.kit_types,
        size_overrides=size_overrides,
        provider=request.provider,
        reference_image_paths=reference_paths,
        image_api_key=request.image_config.get("apiKey", ""),
    )
    logger.info(
        "Generation job created: id=%s provider=%s kit_types=%s product_id=%s",
        job.id,
        request.provider,
        request.kit_types,
        request.product_id,
    )
    asyncio.create_task(job_store.run_job(job.id))
    total = getattr(job, '_total_images', 1)
    return {
        "job_id": job.id,
        "status": job.status,
        "total_images": total,
        "plan_generated": request.run_plan,
    }


@router.get("/jobs")
async def list_jobs():
    return job_store.list_jobs()


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        return job_store.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="找不到任务")


@router.post("/jobs/{job_id}/retry/{kit_type}")
async def retry_generated_image(job_id: str, kit_type: str):
    try:
        job_store.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="找不到任务")

    asyncio.create_task(job_store.retry_kit_type(job_id, kit_type))
    return {"job_id": job_id, "status": "running", "kit_type": kit_type}

class RetouchRequest(BaseModel):
    """图生图编辑：基于当前生成图 + 新提示词 重新生成"""
    image_url: str
    prompt: str
    provider: str = "agnes"
    width: int = 1024
    height: int = 1024


@router.post("/images/retouch")
async def retouch_image(request: RetouchRequest):
    """以当前图为参考 + 新prompt 做图生图重新生成"""

    parsed = urlparse(request.image_url)
    url_path = parsed.path

    if url_path.startswith("/outputs/"):
        rel_path = url_path[len("/outputs/"):]
        local_image_path = OUTPUT_DIR / rel_path
    else:
        local_image_path = Path(url_path)

    if not local_image_path.exists():
        raise HTTPException(status_code=404, detail=f"找不到图片: {local_image_path}")

    provider = create_provider(request.provider)
    RETOUCHED_DIR.mkdir(parents=True, exist_ok=True)
    out_name = f"retouched_{uuid.uuid4().hex[:8]}.png"
    output_path = RETOUCHED_DIR / out_name

    gen_request = ImageGenerationRequest(
        product_image_path=local_image_path,
        output_path=output_path,
        prompt=request.prompt,
        width=request.width,
        height=request.height,
    )

    try:
        result = await provider.generate_image(gen_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

    return {
        "url": f"/outputs/retouched/{out_name}",
        "provider": result.provider,
        "prompt": result.prompt,
    }
