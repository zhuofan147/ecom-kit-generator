from PIL import Image, ImageDraw
import asyncio

import app.services.product_image_analysis as product_image_analysis
from app.services.product_image_analysis import (
    analyze_product_cutout,
    format_product_image_analysis,
)
from app.routers.providers import LlmTestRequest, _chat_completions_url, _models_url, auth_headers, filter_model_ids, list_models
from app.services.imagegen import create_provider, extract_image_url


def test_analyze_product_cutout_extracts_subject_facts(tmp_path):
    image_path = tmp_path / "masked.png"
    image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 30, 79, 69), fill=(32, 32, 32, 255))
    image.save(image_path)

    analysis = analyze_product_cutout(image_path)
    summary = format_product_image_analysis(analysis)

    assert analysis["canvas_width"] == 100
    assert analysis["subject_width"] == 60
    assert analysis["subject_height"] == 40
    assert analysis["has_transparent_background"] is True
    assert "#202020" in analysis["dominant_colors"]
    assert "抠图产品分析" in summary
    assert "主体尺寸约60x40px" in summary
    assert "保持轮廓、比例、材质光泽、色彩、纹理" not in summary


def test_vision_api_uses_shared_ssl_context(monkeypatch, tmp_path):
    image_path = tmp_path / "masked.png"
    Image.new("RGBA", (10, 10), (255, 255, 255, 255)).save(image_path)
    expected_context = object()
    calls = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"{\\"brief_description\\":\\"ok\\",\\"product_type\\":\\"camera\\"}"}}]}'

    def fake_ssl_context():
        return expected_context

    def fake_urlopen(req, timeout=0, context=None):
        calls.append({"timeout": timeout, "context": context})
        return FakeResponse()

    monkeypatch.setattr(product_image_analysis, "ssl_context", fake_ssl_context)
    monkeypatch.setattr(product_image_analysis, "urlopen", fake_urlopen)

    analysis = analyze_product_cutout(
        image_path,
        llm_api_url="https://api.example.com/v1",
        llm_api_key="key",
        llm_model="vision-model",
    )

    assert analysis["vision_analysis"]["brief_description"] == "ok"
    assert calls[0]["context"] is expected_context


def test_filter_model_ids_keeps_only_vision_models_for_vision_cards():
    models = [
        "deepseek-chat",
        "Qwen/Qwen3-VL-32B-Instruct",
        "Qwen3.6-Plus",
        "doubao-seedream-5-0",
    ]

    assert filter_model_ids(models, "vision") == [
        "Qwen/Qwen3-VL-32B-Instruct",
        "Qwen3.6-Plus",
    ]


def test_extract_image_url_accepts_nested_supplier_url_object():
    response = {
        "data": [
            {
                "url": {
                    "url": "https://cdn.example.com/generated.png",
                    "expires_at": 123,
                }
            }
        ]
    }

    assert extract_image_url(response) == "https://cdn.example.com/generated.png"


def test_extract_image_url_accepts_async_result_images_url_list():
    response = {
        "data": [
            {
                "status": "completed",
                "result": {
                    "images": [
                        {
                            "expires_at": 123,
                            "url": ["https://cdn.example.com/generated-from-list.png"],
                        }
                    ]
                },
            }
        ]
    }

    assert extract_image_url(response) == "https://cdn.example.com/generated-from-list.png"


def test_provider_alias_model_override_keeps_registry_model_id():
    provider = create_provider("agnes", model_id_override="agnes")

    assert provider.model_id == "agnes-image-2.0-flash"


def test_filter_model_ids_keeps_only_image_models_for_image_cards():
    models = [
        "deepseek-chat",
        "text-embedding-v3",
        "Qwen/Qwen3-VL-32B-Instruct",
        "agnes-image-2.1-flash",
        "doubao-seedream-5-0-260128",
        "black-forest-labs/FLUX.1-schnell",
        "gpt-image-1",
        "stable-diffusion-xl",
    ]

    assert filter_model_ids(models, "image") == [
        "agnes-image-2.1-flash",
        "doubao-seedream-5-0-260128",
        "black-forest-labs/FLUX.1-schnell",
        "gpt-image-1",
        "stable-diffusion-xl",
    ]


def test_filter_model_ids_leaves_untyped_model_lists_unchanged():
    models = ["deepseek-chat", "Qwen/Qwen3-VL-32B-Instruct"]

    assert filter_model_ids(models, "all") == models


def test_auth_headers_omit_empty_bearer_tokens():
    assert auth_headers("") == {}
    assert auth_headers("   ") == {}
    assert auth_headers("sk-demo") == {"Authorization": "Bearer sk-demo"}


def test_models_url_normalizes_openai_compatible_image_generation_endpoint():
    assert _models_url("https://apihub.agnes-ai.com/v1/images/generations") == (
        "https://apihub.agnes-ai.com/v1/models"
    )


def test_chat_url_normalizes_openai_compatible_image_generation_endpoint():
    assert _chat_completions_url("https://apihub.agnes-ai.com/v1/images/generations") == (
        "https://apihub.agnes-ai.com/v1/chat/completions"
    )


def test_image_list_models_requires_api_key():
    response = asyncio.run(list_models(LlmTestRequest(
        api_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="",
        model_type="image",
    )))

    assert response["models"] == []
    assert response["error"] == "请先填写 API Key"
