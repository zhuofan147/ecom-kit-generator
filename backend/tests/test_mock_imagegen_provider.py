import pytest
from io import BytesIO

from PIL import Image

from app.services.imagegen import ImageGenerationRequest, MockImageGenerationProvider


@pytest.mark.asyncio
async def test_mock_provider_generates_taobao_sized_white_background_image(tmp_path):
    cutout_path = tmp_path / "cutout.png"
    img = Image.new("RGBA", (80, 120), (220, 40, 40, 255))
    img.save(cutout_path)

    output_path = tmp_path / "result.png"
    provider = MockImageGenerationProvider()

    result = await provider.generate_image(
        ImageGenerationRequest(
            product_image_path=cutout_path,
            output_path=output_path,
            prompt="commercial product photo on pure white background",
            width=800,
            height=800,
        )
    )

    assert result.path == output_path
    assert result.provider == "mock"
    with Image.open(BytesIO(output_path.read_bytes())) as generated:
        assert generated.size == (800, 800)
        assert generated.convert("RGB").getpixel((0, 0)) == (255, 255, 255)
