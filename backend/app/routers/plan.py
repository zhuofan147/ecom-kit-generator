"""Product planning API."""

import os

from fastapi import APIRouter

from app.routers.upload import resolve_masked_upload
from app.services.product_image_analysis import analyze_product_cutout
from app.services.plan_engine import (
    PlanRequest,
    ProductPlan,
    create_product_plan,
    get_available_templates,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["plan"])


@router.post("/plan", response_model=ProductPlan)
async def create_plan(request: PlanRequest) -> ProductPlan:
    print(f"PLAN_DEBUG: product_id='{request.product_id}', has_analysis={bool(request.product_image_analysis)}", flush=True)
    if request.product_id and not request.product_image_analysis:
        try:
            request.product_image_analysis = analyze_product_cutout(
                resolve_masked_upload(request.product_id),
                llm_api_url=request.vision_config.get("apiUrl") or os.environ.get("VISION_BASE_URL", "https://api.scnet.cn/api/llm/v1"),
                llm_api_key=request.vision_config.get("apiKey") or os.environ.get("VISION_API_KEY", ""),
                llm_model=request.vision_config.get("model") or os.environ.get("VISION_MODEL", "Qwen3.6-Plus"),
            )
        except KeyError:
            pass
    return create_product_plan(request)


@router.get("/plan/templates")
async def list_plan_templates():
    return get_available_templates()
