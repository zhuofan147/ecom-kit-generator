from app.services.template_engine import (
    KitType,
    ProductInfo,
    build_kit_specs,
    build_prompt,
    get_platform_rule,
    product_info_from_dict,
)


def test_taobao_rule_defaults_to_800_white_background():
    rule = get_platform_rule("taobao")

    assert rule.platform == "taobao"
    assert rule.default_width == 800
    assert rule.default_height == 800
    assert rule.background == "white"


def test_prompt_stitches_product_info_and_platform_rule():
    """Domestic platform uses Chinese, overseas uses English."""
    # Domestic (taobao) → Chinese
    prompt_cn = build_prompt(
        platform="taobao",
        kit_type=KitType.MAIN_WHITE,
        product_info=ProductInfo(
            name="无线蓝牙耳机",
            category="3C",
            material="哑光黑色塑料",
            selling_points=["长续航", "低延迟"],
        ),
    )
    assert "无线蓝牙耳机" in prompt_cn
    assert "哑光黑色塑料" in prompt_cn
    assert "800x800" in prompt_cn
    assert "纯白背景" in prompt_cn

    # Selling points should appear in SELLING_POINT prompt
    prompt_sp = build_prompt(
        platform="taobao",
        kit_type=KitType.SELLING_POINT,
        product_info=ProductInfo(
            name="无线蓝牙耳机",
            selling_points=["长续航", "低延迟"],
        ),
    )
    assert "长续航" in prompt_sp
    assert "低延迟" in prompt_sp

    # Overseas (amazon) → English
    prompt_en = build_prompt(
        platform="amazon",
        kit_type=KitType.MAIN_WHITE,
        product_info=ProductInfo(name="Wireless Earbuds"),
    )
    assert "Wireless Earbuds" in prompt_en
    assert "pure white background" in prompt_en


def test_prompt_includes_product_dimensions():
    prompt = build_prompt(
        platform="taobao",
        kit_type=KitType.SIZE_COMPARE,
        product_info=ProductInfo(
            name="运动相机",
            dimensions="124 x 46 x 38mm，重量 200g",
        ),
    )

    assert "124 x 46 x 38mm，重量 200g" in prompt


def test_kit_specs_generates_all_types():
    specs = build_kit_specs(
        platform="taobao",
        kit_types=[KitType.MAIN_WHITE, KitType.MAIN_SCENE, KitType.SELLING_POINT],
        product_info=product_info_from_dict({"name": "测试"}),
    )
    assert len(specs) == 3
    assert specs[0].kit_type == KitType.MAIN_WHITE
    assert specs[0].width == 800
    assert specs[1].kit_type == KitType.MAIN_SCENE
    assert specs[2].kit_type == KitType.SELLING_POINT


def test_kit_specs_supports_per_type_size_overrides():
    specs = build_kit_specs(
        platform="taobao",
        kit_types=[KitType.MAIN_WHITE],
        product_info=product_info_from_dict({"name": "测试"}),
        size_overrides={KitType.MAIN_WHITE: (1080, 1440)},
    )

    assert specs[0].width == 1080
    assert specs[0].height == 1440
    assert "1080x1440" in specs[0].prompt


def test_all_platforms_load():
    from app.services.template_engine import PLATFORM_RULES
    assert len(PLATFORM_RULES) == 9
    assert "taobao" in PLATFORM_RULES
    assert "amazon" in PLATFORM_RULES
    assert "offline_store" in PLATFORM_RULES


def test_offline_store_rule_builds_vertical_poster_prompt():
    rule = get_platform_rule("offline_store")
    assert rule.label == "其他"
    assert rule.default_width == 1080
    assert rule.default_height == 1440
    assert "offline retail store poster" in rule.requirement

    prompt = build_prompt(
        platform="offline_store",
        kit_type=KitType.MAIN_SCENE,
        product_info=ProductInfo(
            name="门店新品",
            selling_points=["到店体验", "限时优惠"],
            usage_scene="线下门店橱窗",
        ),
    )

    assert "门店新品" in prompt
    assert "线下门店" in prompt
    assert "1080x1440" in prompt


def test_all_kit_types_exist():
    assert len(KitType) == 10
    assert KitType.MAIN_WHITE.value == "main_white"
    assert KitType.VIDEO_COVER.value == "video_cover"


def test_product_info_from_dict_handles_camel_case():
    info = product_info_from_dict({
        "name": "耳机",
        "sellingPoints": "降噪\n防水",
    })
    assert info.name == "耳机"
    assert "降噪" in info.selling_points
    assert "防水" in info.selling_points
