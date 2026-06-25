"""Generation API: create jobs for multi-kit image generation."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import GENERATED_DIR
from app.routers.upload import resolve_masked_upload, resolve_reference_uploads
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
                product_image_analysis=analyze_product_cutout(masked_path),
                image_provider=request.provider,
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
