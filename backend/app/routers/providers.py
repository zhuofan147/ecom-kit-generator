"""Providers API — list available AI image generation providers."""

from fastapi import APIRouter

from app.config.providers import get_provider_list, get_default_provider

router = APIRouter(prefix="/api", tags=["providers"])


@router.get("/providers")
async def list_providers():
    return {
        "providers": get_provider_list(),
        "default": get_default_provider(),
    }
