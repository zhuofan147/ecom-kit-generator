from enum import StrEnum
from pathlib import Path
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GeneratedImage(BaseModel):
    id: str
    file_name: str = ""
    url: str = ""
    prompt: str
    provider: str
    kit_type: str = ""  # e.g. "main_white", "main_scene"
    label: str = ""     # e.g. "白底主图"
    status: str = "completed"
    error: str | None = None


class Job(BaseModel):
    id: str
    product_id: str
    masked_path: Path
    reference_image_paths: list[Path] = Field(default_factory=list)
    platform: str = "taobao"
    product_info: dict = Field(default_factory=dict)
    provider: str = "mock"
    kit_types: list[str] = Field(default_factory=list)
    total_images: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = "等待生成"
    results: list[GeneratedImage] = Field(default_factory=list)
    error: str | None = None
