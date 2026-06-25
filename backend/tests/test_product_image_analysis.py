from PIL import Image, ImageDraw

from app.services.product_image_analysis import (
    analyze_product_cutout,
    format_product_image_analysis,
)


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
