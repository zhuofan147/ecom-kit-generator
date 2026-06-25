"""Product planning API."""

from fastapi import APIRouter

from app.routers.upload import resolve_masked_upload
from app.services.product_image_analysis import analyze_product_cutout
from app.services.plan_engine import (
    PlanRequest,
    ProductPlan,
    create_product_plan,
    get_available_templates,
)

router = APIRouter(prefix="/api", tags=["plan"])


@router.post("/plan", response_model=ProductPlan)
async def create_plan(request: PlanRequest) -> ProductPlan:
    if request.product_id and not request.product_image_analysis:
        try:
            request.product_image_analysis = analyze_product_cutout(
                resolve_masked_upload(request.product_id)
            )
        except KeyError:
            pass
    return create_product_plan(request)


@router.get("/plan/templates")
async def list_plan_templates():
    return get_available_templates()
