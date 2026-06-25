"""Job store: manages generation jobs, supports multi-kit batch generation."""

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.models.job import GeneratedImage, Job, JobStatus
from app.services.imagegen import (
    ImageGenerationProvider,
    ImageGenerationRequest,
    ImageGenerationResult,
    create_provider,
)
from app.services.template_engine import (
    KitType,
    build_kit_specs,
    product_info_from_dict,
)

PRODUCT_CONSISTENCY_PROMPT = (
    "产品一致性硬性要求：保持产品与参考图一致，不得改变产品结构、轮廓、比例、Logo、"
    "材质、光泽、色彩、纹理、花纹、透明度和表面细节；只允许调整背景、构图、光线、"
    "阴影和画面氛围。Preserve the referenced product exactly, including material, sheen, "
    "color, texture, pattern, logo, proportions, and surface details."
)


class JobStore:
    def __init__(self, output_dir: Path,
                  provider_name: str = "mock"):
        self.output_dir = output_dir
        self.history_dir = output_dir / "jobs"
        self.provider_name = provider_name
        self._provider: ImageGenerationProvider | None = None
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._load_jobs()

    @property
    def provider(self) -> ImageGenerationProvider:
        if self._provider is None:
            self._provider = create_provider(self.provider_name)
        return self._provider

    def switch_provider(self, name: str) -> None:
        """Switch provider for subsequent jobs."""
        self.provider_name = name
        self._provider = None  # force re-creation

    def create_generation_job(
        self,
        product_id: str,
        masked_path: Path,
        platform: str,
        product_info: dict | None = None,
        kit_types: list[KitType] | list[str] | None = None,
        size_overrides: dict[KitType, tuple[int, int]] | None = None,
        provider: str | None = None,
        reference_image_paths: list[Path] | None = None,
    ) -> Job:
        # Normalize kit_types to KitType enum
        if kit_types is None:
            kit_types = [KitType.MAIN_WHITE]
        normalized: list[KitType] = []
        for kt in kit_types:
            if isinstance(kt, KitType):
                normalized.append(kt)
            else:
                try:
                    normalized.append(KitType(kt))
                except ValueError:
                    pass

        if not normalized:
            normalized = [KitType.MAIN_WHITE]

        job = Job(
            id=uuid4().hex,
            product_id=product_id,
            masked_path=masked_path,
            reference_image_paths=reference_image_paths or [],
            platform=platform,
            product_info=product_info or {},
            provider=provider or self.provider_name,
            kit_types=[kit_type.value for kit_type in normalized],
            total_images=len(normalized),
        )
        object.__setattr__(job, '_kit_types', normalized)
        object.__setattr__(job, '_total_images', len(normalized))
        object.__setattr__(job, '_provider', provider or self.provider_name)
        object.__setattr__(job, '_size_overrides', size_overrides or {})
        self._jobs[job.id] = job
        self._save_job(job)
        return job

    def get(self, job_id: str) -> Job:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"Unknown job: {job_id}") from exc

    def list_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def _job_path(self, job_id: str) -> Path:
        return self.history_dir / f"{job_id}.json"

    def _save_job(self, job: Job) -> None:
        self.history_dir.mkdir(parents=True, exist_ok=True)
        job.updated_at = datetime.now(timezone.utc).isoformat()
        self._job_path(job.id).write_text(
            json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load_jobs(self) -> None:
        if not self.history_dir.exists():
            return
        for path in sorted(self.history_dir.glob("*.json")):
            try:
                job = Job.model_validate_json(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if job.status in {JobStatus.PENDING, JobStatus.RUNNING}:
                job.status = JobStatus.FAILED
                job.progress = 100
                job.message = "服务重启，任务已中断"
                job.error = "服务重启后，未完成的生成任务无法继续。请重新生成。"
                self._save_job(job)
            self._jobs[job.id] = job

    async def run_job(self, job_id: str) -> None:
        async with self._lock:
            job = self.get(job_id)
            job.status = JobStatus.RUNNING
            job.progress = 5
            job.message = "正在分析产品信息…"
            self._save_job(job)

            # Determine provider for this job
            prov_name = getattr(job, '_provider', self.provider_name)
            if prov_name != self.provider_name:
                self.switch_provider(prov_name)

            try:
                kit_types: list[KitType] = getattr(job, '_kit_types', [KitType.MAIN_WHITE])
                size_overrides = getattr(job, '_size_overrides', {})
                product_info = product_info_from_dict(job.product_info)
                specs = build_kit_specs(
                    job.platform,
                    kit_types,
                    product_info,
                    size_overrides=size_overrides,
                )
                specs = apply_planned_prompts(specs, job.product_info)
                total = len(specs)

                job.progress = 10
                job.message = f"准备生成 {total} 张套图（{self.provider_name}）"
                self._save_job(job)

                # 并行并发控制：最多3张同时生成
                sem = asyncio.Semaphore(3)
                results: list[GeneratedImage | None] = [None] * total  # 预分配保证顺序
                completed_count = 0

                async def gen_one(idx: int, spec):
                    nonlocal completed_count
                    async with sem:
                        job.message = f"正在生成 {spec.label}（{idx + 1}/{total}）"
                        file_name = f"{job.id}_{spec.file_suffix}.png"
                        output_path = self.output_dir / file_name

                        try:
                            results[idx] = await self._generate_spec_result(
                                masked_path=job.masked_path,
                                reference_image_paths=job.reference_image_paths,
                                output_path=output_path,
                                spec=spec,
                                product_info=product_info,
                            )
                        except Exception as exc:
                            results[idx] = self._failed_result(spec, str(exc))
                        finally:
                            completed_count += 1
                            job.progress = 10 + int((completed_count / total) * 80)
                            self._save_job(job)

                await asyncio.gather(*[gen_one(i, s) for i, s in enumerate(specs)])

                job.results = [result for result in results if result is not None]
                job.status = JobStatus.COMPLETED
                job.progress = 100
                failed = sum(1 for result in job.results if result.status == "failed")
                succeeded = len(job.results) - failed
                job.message = (
                    f"生成完成，成功 {succeeded} 张，失败 {failed} 张（{self.provider_name}）"
                    if failed else
                    f"生成完成，共 {len(job.results)} 张套图（{self.provider_name}）"
                )
                self._save_job(job)
            except Exception as exc:
                job.status = JobStatus.FAILED
                job.error = str(exc)
                job.message = "生成失败"
                self._save_job(job)
                raise

    async def retry_kit_type(self, job_id: str, kit_type: str) -> None:
        async with self._lock:
            job = self.get(job_id)
            prov_name = getattr(job, '_provider', self.provider_name)
            if prov_name != self.provider_name:
                self.switch_provider(prov_name)

            specs = self._build_specs(job)
            spec = next((item for item in specs if item.kit_type.value == kit_type), None)
            if spec is None:
                raise KeyError(f"Unknown kit type for job: {kit_type}")

            product_info = product_info_from_dict(job.product_info)
            job.status = JobStatus.RUNNING
            job.progress = 20
            job.message = f"正在重新生成 {spec.label}"
            self._replace_result(job, GeneratedImage(
                id=uuid4().hex,
                prompt=spec.prompt,
                provider=self.provider_name,
                kit_type=spec.kit_type.value,
                label=spec.label,
                status="running",
            ))
            self._save_job(job)

            file_name = f"{job.id}_{spec.file_suffix}_{uuid4().hex[:8]}.png"
            output_path = self.output_dir / file_name
            try:
                result = await self._generate_spec_result(
                    masked_path=job.masked_path,
                    reference_image_paths=job.reference_image_paths,
                    output_path=output_path,
                    spec=spec,
                    product_info=product_info,
                )
            except Exception as exc:
                result = self._failed_result(spec, str(exc))

            self._replace_result(job, result)
            failed = sum(1 for item in job.results if item.status == "failed")
            succeeded = sum(1 for item in job.results if item.status == "completed")
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.message = (
                f"重新生成完成，成功 {succeeded} 张，失败 {failed} 张"
                if failed else
                f"重新生成完成，成功 {succeeded} 张"
            )
            self._save_job(job)

    def _build_specs(self, job: Job):
        kit_types: list[KitType] = getattr(job, '_kit_types', [KitType.MAIN_WHITE])
        size_overrides = getattr(job, '_size_overrides', {})
        product_info = product_info_from_dict(job.product_info)
        specs = build_kit_specs(
            job.platform,
            kit_types,
            product_info,
            size_overrides=size_overrides,
        )
        return apply_planned_prompts(specs, job.product_info)

    def _replace_result(self, job: Job, next_result: GeneratedImage) -> None:
        replaced = False
        next_results: list[GeneratedImage] = []
        for result in job.results:
            if result.kit_type == next_result.kit_type:
                next_results.append(next_result)
                replaced = True
            else:
                next_results.append(result)
        if not replaced:
            next_results.append(next_result)
        job.results = next_results

    async def _generate_spec_result(
        self,
        masked_path: Path,
        reference_image_paths: list[Path],
        output_path: Path,
        spec,
        product_info,
    ) -> GeneratedImage:
        result = await self._generate_one(
            masked_path=masked_path,
            reference_image_paths=reference_image_paths,
            output_path=output_path,
            spec=spec,
            product_info=product_info,
        )
        return GeneratedImage(
            id=uuid4().hex,
            file_name=result.path.name,
            url=f"/outputs/generated/{result.path.name}",
            prompt=result.prompt,
            provider=result.provider,
            kit_type=spec.kit_type.value,
            label=spec.label,
            status="completed",
        )

    def _failed_result(self, spec, error: str) -> GeneratedImage:
        return GeneratedImage(
            id=uuid4().hex,
            prompt=spec.prompt,
            provider=self.provider_name,
            kit_type=spec.kit_type.value,
            label=spec.label,
            status="failed",
            error=error,
        )

    async def _generate_one(
        self,
        masked_path: Path,
        reference_image_paths: list[Path],
        output_path: Path,
        spec,
        product_info,
    ) -> ImageGenerationResult:
        provider = self.provider
        generation_request = ImageGenerationRequest(
            product_image_path=masked_path,
            output_path=output_path,
            prompt=append_reference_image_guidance(spec.prompt, reference_image_paths),
            width=spec.width,
            height=spec.height,
            reference_image_paths=reference_image_paths,
            kit_type=spec.kit_type,
            product_name=product_info.name,
            selling_points=product_info.selling_points,
            brand_tone=product_info.brand_tone,
        )

        def run_provider() -> ImageGenerationResult:
            return asyncio.run(provider.generate_image(generation_request))

        return await asyncio.to_thread(run_provider)


def apply_planned_prompts(specs, product_info: dict | None):
    planned = (product_info or {}).get("planned_prompts") or {}
    if not isinstance(planned, dict):
        return [
            replace(spec, prompt=append_product_consistency(spec.prompt))
            for spec in specs
        ]
    return [
        replace(
            spec,
            prompt=append_product_consistency(
                fuse_planned_prompt(spec.prompt, planned.get(spec.kit_type.value))
            ),
        )
        for spec in specs
    ]


def fuse_planned_prompt(default_prompt: str, planned_prompt: str | None) -> str:
    if not isinstance(planned_prompt, str) or not planned_prompt.strip():
        return default_prompt
    return (
        f"{default_prompt}\n\n"
        f"结构化方案优化补充：在保持以上平台规范、套图类型要求和产品一致性约束的基础上，"
        f"融合以下创意方案优化画面质量、卖点表达和构图层次：{planned_prompt.strip()}"
    )


def append_product_consistency(prompt: str) -> str:
    if PRODUCT_CONSISTENCY_PROMPT in prompt:
        return prompt
    return f"{prompt}\n\n{PRODUCT_CONSISTENCY_PROMPT}"


def append_reference_image_guidance(prompt: str, reference_image_paths: list[Path]) -> str:
    if len(reference_image_paths) <= 1 or "多角度参考图要求" in prompt:
        return prompt
    return (
        f"{prompt}\n\n"
        f"多角度参考图要求：本次提供了{len(reference_image_paths)}张产品参考图。"
        "必须综合所有参考图保持商品真实结构、正面/侧面/背面比例、镜头/按钮/接口位置、"
        "品牌文字和Logo位置一致；不得把参考图中的文字生成成乱码，不确定的文字区域保持干净留白。"
    )
