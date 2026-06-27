"""Product planning API."""

from fastapi import APIRouter, HTTPException

from app.routers.upload import resolve_masked_upload
from app.services.product_image_analysis import analyze_product_cutout
from app.services.plan_engine import (
    PlanConfigurationError,
    PlanRequest,
    ProductPlan,
    create_product_plan,
    get_available_templates,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["plan"])


def _has_complete_model_config(config: dict | None) -> bool:
    return bool(
        config
        and str(config.get("apiUrl") or "").strip()
        and str(config.get("apiKey") or "").strip()
        and str(config.get("model") or "").strip()
    )


@router.post("/plan", response_model=ProductPlan)
async def create_plan(request: PlanRequest) -> ProductPlan:
    # DEBUG: log incoming vision_config
    print(f"[PLAN_DEBUG] vision_config={request.vision_config}", flush=True)
    print(f"[PLAN_DEBUG] vision_model={request.vision_config.get('model', 'MISSING')!r}", flush=True)
    print(f"PLAN_DEBUG: product_id='{request.product_id}', has_analysis={bool(request.product_image_analysis)}", flush=True)
    if request.product_id and not request.product_image_analysis:
        if not _has_complete_model_config(request.vision_config):
            raise HTTPException(status_code=400, detail="请先在设置中配置视觉模型：商家、base_url、API Key 和模型名称都不能为空")
        try:
            analysis = analyze_product_cutout(
                resolve_masked_upload(request.product_id),
                llm_api_url=request.vision_config.get("apiUrl"),
                llm_api_key=request.vision_config.get("apiKey"),
                llm_model=request.vision_config.get("model"),
            )
            if not analysis.get("vision_analysis"):
                raise HTTPException(status_code=400, detail="视觉模型调用失败，请检查视觉模型的 base_url、API Key 和模型名称")
            request.product_image_analysis = analysis
        except KeyError:
            pass
    try:
        return create_product_plan(request)
    except PlanConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/plan/templates")
async def list_plan_templates():
    return get_available_templates()
