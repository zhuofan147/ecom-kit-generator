import math
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.config import UPLOAD_DIR
from app.services.rembg_service import BackgroundRemovalService

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_REFERENCE_IMAGES = 6


@router.post("/upload")
async def upload_product_image(
    file: UploadFile | None = File(None),
    files: list[UploadFile] | None = File(None),
):
    upload_files = files or ([file] if file else [])
    if not upload_files:
        raise HTTPException(status_code=400, detail="请至少上传 1 张产品图")
    if len(upload_files) > MAX_REFERENCE_IMAGES:
        raise HTTPException(status_code=400, detail=f"参考图最多支持 {MAX_REFERENCE_IMAGES} 张")

    primary_file = upload_files[0]
    extension = ALLOWED_CONTENT_TYPES.get(primary_file.content_type or "")
    if not extension:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 图片")

    primary_content = await primary_file.read()
    if len(primary_content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 20MB")

    product_id = uuid4().hex
    product_dir = UPLOAD_DIR / product_id
    refs_dir = product_dir / "references"
    product_dir.mkdir(parents=True, exist_ok=True)
    refs_dir.mkdir(parents=True, exist_ok=True)
    original_path = product_dir / f"original{extension}"
    masked_path = product_dir / "masked.png"
    mask_path = product_dir / "mask.png"
    white_path = product_dir / "white.png"
    multi_view_path = product_dir / "multi_view.png"
    original_path.write_bytes(primary_content)

    removal_service = BackgroundRemovalService()
    removal_service.remove_background(original_path, masked_path, mask_path)
    _render_white_background(masked_path, white_path)

    reference_paths = [white_path]
    for index, ref_file in enumerate(upload_files[1:], start=1):
        ref_extension = ALLOWED_CONTENT_TYPES.get(ref_file.content_type or "")
        if not ref_extension:
            raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 图片")
        ref_content = await ref_file.read()
        if len(ref_content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="图片不能超过 20MB")
        ref_path = refs_dir / f"ref_{index}{ref_extension}"
        ref_path.write_bytes(ref_content)

        ref_masked_path = refs_dir / f"ref_{index}_masked.png"
        ref_mask_path = refs_dir / f"ref_{index}_mask.png"
        ref_white_path = refs_dir / f"ref_{index}_white.png"
        removal_service.remove_background(ref_path, ref_masked_path, ref_mask_path)
        _render_white_background(ref_masked_path, ref_white_path)
        reference_paths.append(ref_white_path)

    _compose_multi_view(reference_paths, multi_view_path)

    return {
        "product_id": product_id,
        "original_url": _url_for_upload(product_id, original_path),
        "masked_url": _url_for_upload(product_id, masked_path),
        "mask_url": _url_for_upload(product_id, mask_path),
        "reference_urls": [_url_for_upload(product_id, path) for path in reference_paths],
        "multi_view_url": _url_for_upload(product_id, multi_view_path),
    }


@router.post("/upload/single")
async def upload_single_product_image(file: UploadFile = File(...)):
    extension = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if not extension:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 图片")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 20MB")

    product_id = uuid4().hex
    product_dir = UPLOAD_DIR / product_id
    product_dir.mkdir(parents=True, exist_ok=True)
    original_path = product_dir / f"original{extension}"
    masked_path = product_dir / "masked.png"
    mask_path = product_dir / "mask.png"
    white_path = product_dir / "white.png"
    multi_view_path = product_dir / "multi_view.png"
    original_path.write_bytes(content)

    BackgroundRemovalService().remove_background(original_path, masked_path, mask_path)
    _render_white_background(masked_path, white_path)
    _compose_multi_view([white_path], multi_view_path)

    return {
        "product_id": product_id,
        "original_url": _url_for_upload(product_id, original_path),
        "masked_url": _url_for_upload(product_id, masked_path),
        "mask_url": _url_for_upload(product_id, mask_path),
        "reference_urls": [_url_for_upload(product_id, white_path)],
        "multi_view_url": _url_for_upload(product_id, multi_view_path),
    }


def resolve_masked_upload(product_id: str) -> Path:
    masked_path = UPLOAD_DIR / product_id / "masked.png"
    if not masked_path.exists():
        raise KeyError(product_id)
    return masked_path


def resolve_reference_uploads(product_id: str) -> list[Path]:
    product_dir = UPLOAD_DIR / product_id
    if not product_dir.exists():
        raise KeyError(product_id)

    multi_view_path = product_dir / "multi_view.png"
    if multi_view_path.exists():
        return [multi_view_path]

    paths = sorted(product_dir.glob("original.*"))
    refs_dir = product_dir / "references"
    if refs_dir.exists():
        paths.extend(sorted(refs_dir.glob("ref_*.*")))
    return paths


def _render_white_background(masked_path: Path, white_path: Path) -> None:
    with Image.open(masked_path) as image:
        rgba = image.convert("RGBA")
        canvas = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        canvas.alpha_composite(rgba)
        canvas.convert("RGB").save(white_path, format="PNG")


def _compose_multi_view(image_paths: list[Path], output_path: Path) -> None:
    if not image_paths:
        return

    tiles: list[Image.Image] = []
    tile_size = 720
    padding = 48
    for path in image_paths[:MAX_REFERENCE_IMAGES]:
        with Image.open(path) as image:
            tile = Image.new("RGB", (tile_size, tile_size), "white")
            product = image.convert("RGB")
            product.thumbnail((tile_size - padding * 2, tile_size - padding * 2), Image.Resampling.LANCZOS)
            x = (tile_size - product.width) // 2
            y = (tile_size - product.height) // 2
            tile.paste(product, (x, y))
            tiles.append(tile)

    columns = min(3, len(tiles))
    rows = math.ceil(len(tiles) / columns)
    gap = 24
    width = columns * tile_size + (columns + 1) * gap
    height = rows * tile_size + (rows + 1) * gap
    canvas = Image.new("RGB", (width, height), "white")
    for index, tile in enumerate(tiles):
        col = index % columns
        row = index // columns
        canvas.paste(tile, (gap + col * (tile_size + gap), gap + row * (tile_size + gap)))
    canvas.save(output_path, format="PNG")


def _url_for_upload(product_id: str, path: Path) -> str:
    try:
        relative = path.relative_to(UPLOAD_DIR / product_id)
    except ValueError:
        relative = Path(path.name)
    return f"/outputs/uploads/{product_id}/{relative.as_posix()}"
