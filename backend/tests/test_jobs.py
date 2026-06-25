import asyncio
import time

from PIL import Image

from app.models.job import JobStatus
from app.services.jobs import JobStore
from app.services.imagegen import ImageGenerationProvider, ImageGenerationRequest, ImageGenerationResult


class PartiallyFailingProvider(ImageGenerationProvider):
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if request.kit_type.value == "main_scene":
            raise RuntimeError("scene provider failed")
        Image.new("RGBA", (request.width, request.height), (30, 160, 210, 255)).save(request.output_path)
        return ImageGenerationResult(
            path=request.output_path,
            provider="partial",
            prompt=request.prompt,
        )


class BlockingProvider(ImageGenerationProvider):
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        time.sleep(0.2)
        Image.new("RGBA", (request.width, request.height), (40, 80, 120, 255)).save(request.output_path)
        return ImageGenerationResult(path=request.output_path, provider="blocking", prompt=request.prompt)


class CapturingProvider(ImageGenerationProvider):
    def __init__(self):
        self.reference_count = 0

    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        self.reference_count = len(request.reference_image_paths)
        Image.new("RGBA", (request.width, request.height), (40, 80, 120, 255)).save(request.output_path)
        return ImageGenerationResult(path=request.output_path, provider="capture", prompt=request.prompt)


def test_job_store_runs_generation_task_to_completion(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
    )

    asyncio.run(store.run_job(job.id))

    completed = store.get(job.id)
    assert completed.status == JobStatus.COMPLETED
    assert completed.progress == 100
    assert len(completed.results) == 1
    assert (tmp_path / completed.results[0].file_name).exists()


def test_job_store_lists_created_jobs(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    first = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
    )
    second = store.create_generation_job(
        product_id="product-2",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品2"},
    )

    assert [job.id for job in store.list_jobs()] == [first.id, second.id]


def test_job_store_persists_completed_jobs_for_history(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
        kit_types=["main_white"],
        provider="mock",
    )
    asyncio.run(store.run_job(job.id))

    restored_store = JobStore(output_dir=tmp_path)
    restored = restored_store.get(job.id)

    assert restored.id == job.id
    assert restored.status == JobStatus.COMPLETED
    assert restored.product_info["name"] == "测试商品"
    assert restored.results[0].status == "completed"
    assert restored.results[0].url.startswith("/outputs/generated/")


def test_job_store_marks_interrupted_running_jobs_failed_on_restore(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
        kit_types=["main_white"],
    )
    job.status = JobStatus.RUNNING
    job.message = "正在生成"
    store._save_job(job)

    restored_store = JobStore(output_dir=tmp_path)
    restored = restored_store.get(job.id)

    assert restored.status == JobStatus.FAILED
    assert restored.progress == 100
    assert "服务重启" in restored.message


def test_job_store_fuses_planned_prompt_with_default_prompt(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={
            "name": "测试商品",
            "planned_prompts": {
                "main_white": "六段式规划提示词：主标题 测试卖点",
            },
        },
        kit_types=["main_white"],
    )

    asyncio.run(store.run_job(job.id))

    completed = store.get(job.id)
    prompt = completed.results[0].prompt
    assert "电商产品摄影图，主体：测试商品" in prompt
    assert "严格保持参考图外形、颜色、材质、比例不变" in prompt
    assert "六段式规划提示词：主标题 测试卖点" in prompt
    assert "保持产品与参考图一致" in prompt
    assert "材质" in prompt
    assert "光泽" in prompt
    assert "色彩" in prompt
    assert "纹理" in prompt


def test_job_store_keeps_successful_images_when_one_type_fails(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    store._provider = PartiallyFailingProvider()
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
        kit_types=["main_white", "main_scene"],
    )

    asyncio.run(store.run_job(job.id))

    completed = store.get(job.id)
    assert completed.status == JobStatus.COMPLETED
    assert len(completed.results) == 2
    assert completed.results[0].kit_type == "main_white"
    assert completed.results[0].status == "completed"
    assert (tmp_path / completed.results[0].file_name).exists()
    assert completed.results[1].kit_type == "main_scene"
    assert completed.results[1].status == "failed"
    assert "scene provider failed" in completed.results[1].error


def test_job_store_can_retry_one_failed_kit_type(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    store = JobStore(output_dir=tmp_path)
    store._provider = PartiallyFailingProvider()
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
        kit_types=["main_scene"],
    )
    asyncio.run(store.run_job(job.id))
    assert store.get(job.id).results[0].status == "failed"

    store._provider = PartiallyFailingProvider()
    async def successful_generate(request: ImageGenerationRequest) -> ImageGenerationResult:
        Image.new("RGBA", (request.width, request.height), (10, 20, 30, 255)).save(request.output_path)
        return ImageGenerationResult(path=request.output_path, provider="retry", prompt=request.prompt)

    store._provider.generate_image = successful_generate
    asyncio.run(store.retry_kit_type(job.id, "main_scene"))

    retried = store.get(job.id).results[0]
    assert retried.status == "completed"
    assert retried.provider == "retry"
    assert (tmp_path / retried.file_name).exists()


def test_job_store_does_not_block_event_loop_during_provider_call(tmp_path):
    product_path = tmp_path / "product.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)

    async def run_check():
        store = JobStore(output_dir=tmp_path)
        store._provider = BlockingProvider()
        job = store.create_generation_job(
            product_id="product-1",
            masked_path=product_path,
            platform="taobao",
            product_info={"name": "测试商品"},
            kit_types=["main_white"],
        )

        task = asyncio.create_task(store.run_job(job.id))
        started = time.perf_counter()
        await asyncio.sleep(0.05)
        elapsed = time.perf_counter() - started
        await task
        return elapsed

    assert asyncio.run(run_check()) < 0.12


def test_job_store_passes_reference_images_to_provider(tmp_path):
    product_path = tmp_path / "product.png"
    ref_path = tmp_path / "side.png"
    Image.new("RGBA", (120, 120), (30, 160, 210, 255)).save(product_path)
    Image.new("RGBA", (120, 120), (210, 160, 30, 255)).save(ref_path)

    provider = CapturingProvider()
    store = JobStore(output_dir=tmp_path)
    store._provider = provider
    job = store.create_generation_job(
        product_id="product-1",
        masked_path=product_path,
        platform="taobao",
        product_info={"name": "测试商品"},
        kit_types=["main_white"],
        reference_image_paths=[product_path, ref_path],
    )

    asyncio.run(store.run_job(job.id))

    assert provider.reference_count == 2
