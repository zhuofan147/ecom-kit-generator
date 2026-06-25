import pytest

from app.main import app
from app.services.plan_engine import (
    TEMPLATE_DETAIL,
    TEMPLATE_SCENE,
    TEMPLATE_SELLING_POINT,
    TEMPLATE_SIZE_COMPARE,
    TEMPLATE_USE_SCENE,
    TEMPLATE_WHITE_BG,
    PlanRequest,
    _AI_PLAN_SYSTEM_PROMPT,
    _build_product_plan_from_ai,
    _build_chat_completions_url,
    _get_plan_ai_client,
    build_layer1,
    build_layer3,
    create_product_plan,
    fuse_final_plan_prompt,
    get_template,
)


def test_tokenplan_plan_ai_client_uses_glm52_and_keeps_v1_base_url(monkeypatch):
    monkeypatch.setenv("TOKENPLAN_API_KEY", "test-token")
    monkeypatch.setenv("TOKENPLAN_BASE_URL", "https://api.scnet.cn/api/llm/v1")
    monkeypatch.delenv("PLAN_AI_MODEL", raising=False)

    api_key, base_url, default_model = _get_plan_ai_client()

    assert api_key == "test-token"
    assert base_url == "https://api.scnet.cn/api/llm/v1"
    assert default_model == "glm-5.2"
    assert _build_chat_completions_url(base_url) == "https://api.scnet.cn/api/llm/v1/chat/completions"


def get_test_client():
    pytest.importorskip("httpx2")
    from fastapi.testclient import TestClient
    return TestClient(app)


def test_plan_engine_returns_five_points_and_five_image_plans(monkeypatch):
    monkeypatch.setenv("PLAN_ENGINE_MODE", "rule")
    request = PlanRequest(
        product_name="无线蓝牙耳机",
        product_price="199",
        target_audience="通勤上班族",
        usage_scene="地铁通勤和办公室会议",
        selling_points="主动降噪\n40小时续航\n低延迟游戏模式\n轻盈佩戴\nType-C快充",
        competitor_diff="比同价位耳机续航更久，佩戴更轻",
        platform="taobao",
    )

    plan = create_product_plan(request)

    assert len(plan.refined_selling_points) == 5
    assert len(plan.image_plans) == 5
    assert plan.image_plans[0].index == 1
    assert len(plan.image_plans[0].main_title) <= 8
    assert len(plan.image_plans[0].subtitle) <= 15
    assert plan.image_plans[0].kit_type == "main_white"
    assert plan.image_plans[0].ai_prompt.startswith(build_layer1())
    assert "Pure white background RGB(255,255,255)" in plan.image_plans[0].ai_prompt
    assert plan.image_plans[0].ai_prompt.endswith(build_layer3())
    assert plan.mobile_checklist
    assert plan.conversion_checklist


def test_plan_engine_uses_selected_kit_types(monkeypatch):
    monkeypatch.setenv("PLAN_ENGINE_MODE", "rule")
    request = PlanRequest(
        product_name="无线蓝牙耳机",
        selling_points="主动降噪\n40小时续航",
        platform="taobao",
        kit_types=["main_white", "detail_page", "video_cover"],
    )

    plan = create_product_plan(request)

    assert [item.kit_type for item in plan.image_plans] == [
        "main_white",
        "detail_page",
        "video_cover",
    ]


def test_plan_engine_uses_selected_kit_size_without_injecting_old_prefix(monkeypatch):
    monkeypatch.setenv("PLAN_ENGINE_MODE", "rule")
    request = PlanRequest(
        product_name="无线蓝牙耳机",
        platform="taobao",
        kit_types=["detail_page"],
        kit_sizes={"detail_page": {"w": 1080, "h": 1920}},
    )

    plan = create_product_plan(request)

    assert plan.image_plans[0].kit_type == "detail_page"
    assert plan.image_plans[0].ai_prompt.startswith(build_layer1())
    assert "1080x1920" not in plan.image_plans[0].ai_prompt
    assert "图生图任务" not in plan.image_plans[0].ai_prompt


def test_plan_prompt_excludes_cutout_analysis_from_final_prompt(monkeypatch):
    monkeypatch.setenv("PLAN_ENGINE_MODE", "rule")
    request = PlanRequest(
        product_name="无线蓝牙耳机",
        platform="taobao",
        kit_types=["main_scene"],
        product_image_analysis={
            "subject_width": 420,
            "subject_height": 360,
            "subject_aspect": 1.17,
            "subject_coverage": 0.42,
            "dominant_colors": ["#202020", "#C0C0C0"],
        },
    )

    plan = create_product_plan(request)
    prompt = plan.image_plans[0].ai_prompt

    assert prompt.startswith(build_layer1())
    assert "抠图产品分析" not in prompt
    assert "#202020" not in prompt
    assert "只重构背景、光线、阴影、构图和氛围" not in prompt


def test_ai_plan_prompt_fuses_ai_layer2_between_fixed_layers_without_analysis():
    request = PlanRequest(
        product_name="无线蓝牙耳机",
        platform="taobao",
        kit_types=["main_scene"],
        product_image_analysis={
            "subject_width": 420,
            "subject_height": 360,
            "subject_aspect": 1.17,
            "subject_coverage": 0.42,
            "dominant_colors": ["#202020"],
        },
    )

    plan = _build_product_plan_from_ai(
        {
            "refined_selling_points": ["降噪"],
            "image_plans": [
                {
                    "index": 1,
                    "main_title": "清晰降噪",
                    "subtitle": "通勤更安静",
                    "visual_suggestion": "放在桌面上",
                    "ai_prompt": "generic product poster",
                    "kit_type": "main_scene",
                }
            ],
        },
        request,
    )

    prompt = plan.image_plans[0].ai_prompt
    assert prompt == f"{build_layer1()} generic product poster {build_layer3()}"
    assert "抠图产品分析" not in prompt
    assert "#202020" not in prompt
    assert "图生图任务" not in prompt


def test_v3_prompt_framework_fuses_layers_without_analysis_or_old_prefix():
    request = PlanRequest(
        product_name="无线蓝牙耳机",
        platform="taobao",
        kit_types=["main_scene"],
        product_image_analysis={
            "subject_width": 420,
            "subject_height": 360,
            "subject_aspect": 1.17,
            "subject_coverage": 0.42,
            "dominant_colors": ["#202020"],
        },
    )

    plan = _build_product_plan_from_ai(
        {
            "refined_selling_points": ["降噪"],
            "image_plans": [
                {
                    "index": 1,
                    "main_title": "清晰降噪",
                    "subtitle": "通勤更安静",
                    "visual_suggestion": "通勤桌面",
                    "ai_prompt": "Earbuds placed in a commuter desk setup. Surrounding props: notebook and coffee to build atmosphere. Product remains visual center. Scene title \"Quiet Commute\" at top-left. 85mm f/1.4, shallow depth of field, warm natural lighting.",
                    "kit_type": "main_scene",
                }
            ],
        },
        request,
    )

    prompt = plan.image_plans[0].ai_prompt
    assert prompt == (
        f"{build_layer1()} "
        "Earbuds placed in a commuter desk setup. Surrounding props: notebook and coffee to build atmosphere. Product remains visual center. Scene title \"Quiet Commute\" at top-left. 85mm f/1.4, shallow depth of field, warm natural lighting. "
        f"{build_layer3()}"
    )
    assert "抠图产品分析" not in prompt
    assert "#202020" not in prompt
    assert "Generate" not in prompt
    assert "based on" not in prompt
    assert "no props" not in prompt.lower()
    assert "no text" not in prompt.lower()


def test_v3_templates_are_available_by_alias_and_ai_prompt_requires_template_fill():
    assert get_template("white_bg") == TEMPLATE_WHITE_BG
    assert get_template("白底主图") == TEMPLATE_WHITE_BG
    assert get_template("selling_point") == TEMPLATE_SELLING_POINT
    assert get_template("卖点主图") == TEMPLATE_SELLING_POINT
    assert get_template("scene") == TEMPLATE_SCENE
    assert get_template("场景主图") == TEMPLATE_SCENE
    assert get_template("detail") == TEMPLATE_DETAIL
    assert get_template("细节特写") == TEMPLATE_DETAIL
    assert get_template("size_compare") == TEMPLATE_SIZE_COMPARE
    assert get_template("尺寸对比") == TEMPLATE_SIZE_COMPARE
    assert get_template("use_scene") == TEMPLATE_USE_SCENE
    assert get_template("使用场景") == TEMPLATE_USE_SCENE

    final_prompt = fuse_final_plan_prompt("white_bg", TEMPLATE_WHITE_BG)
    assert final_prompt == f"{build_layer1()} {TEMPLATE_WHITE_BG} {build_layer3()}"
    assert "基于模板填空" in _AI_PLAN_SYSTEM_PROMPT
    assert "不改变结构" in _AI_PLAN_SYSTEM_PROMPT


def test_core_kit_prompts_follow_img2img_reference_lock_rules(monkeypatch):
    monkeypatch.setenv("PLAN_ENGINE_MODE", "rule")
    request = PlanRequest(
        product_name="手机壳",
        target_audience="年轻用户",
        usage_scene="节日桌面和日常手持使用",
        selling_points="防摔缓震\n镜头保护\n不易发黄\n手感轻薄\n贴合按键",
        platform="taobao",
        kit_types=["main_white", "selling_point", "main_scene", "detail", "usage_scene"],
    )

    plan = create_product_plan(request)
    prompts = {item.kit_type: item.ai_prompt for item in plan.image_plans}

    for prompt in prompts.values():
        assert prompt.startswith(build_layer1())
        assert prompt.endswith(build_layer3())
        assert "DONT" not in prompt
        assert "DO NOT" not in prompt
        assert "Generate" not in prompt
        assert "based on" not in prompt
        assert "no props" not in prompt.lower()
        assert "no text" not in prompt.lower()
        assert "主体：手机壳" not in prompt

    assert "Pure white background RGB(255,255,255)" in prompts["main_white"]
    assert "Commercial product photography style" in prompts["main_white"]

    assert "Annotation arrows pointing to" in prompts["selling_point"]
    assert "Callout boxes with clean text layout" in prompts["selling_point"]
    assert "Core benefit" in prompts["selling_point"]

    assert "节日桌面和日常手持使用" in prompts["main_scene"]
    assert "85mm f/1.4" in prompts["main_scene"]

    assert "Zoom-in on" in prompts["detail"]
    assert "10x magnification" in prompts["detail"]
    assert "Material label" in prompts["detail"]

    assert "Person naturally using" in prompts["usage_scene"]
    assert "Candid photography style" in prompts["usage_scene"]


def test_plan_api_templates_returns_available_categories():
    client = get_test_client()

    response = client.get("/api/plan/templates")

    assert response.status_code == 200
    body = response.json()
    assert "categories" in body
    assert "3C" in body["categories"]
    assert "kit_types" in body


def test_plan_api_creates_product_plan():
    client = get_test_client()

    response = client.post(
        "/api/plan",
        json={
            "product_name": "玻璃保鲜盒",
            "product_price": "59",
            "target_audience": "家庭用户",
            "usage_scene": "厨房收纳和带饭",
            "selling_points": "耐热玻璃，密封防漏，容易清洗",
            "competitor_diff": "盖子更紧，不串味",
            "platform": "jd",
            "kit_types": ["main_scene", "selling_point"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["refined_selling_points"]) == 5
    assert len(body["image_plans"]) == 2
    assert [item["kit_type"] for item in body["image_plans"]] == ["main_scene", "selling_point"]
