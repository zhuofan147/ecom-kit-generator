from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class BackgroundRemovalResult:
    original_path: Path
    masked_path: Path
    mask_path: Path


class BackgroundRemovalService:
    def __init__(self):
        self._model_loaded = False

    def _ensure_model(self):
        """Pre-load rembg model once (downloads ~176MB on first call)."""
        if self._model_loaded:
            return
        try:
            from rembg import remove, new_session
            # Trigger model download by running on a tiny image
            from PIL import Image
            tiny = Image.new("RGB", (64, 64), (128, 128, 128))
            remove(tiny, session=new_session("u2net"))
        except Exception:
            pass  # will fall back at actual remove time
        self._model_loaded = True

    def remove_background(self, original_path: Path, masked_path: Path, mask_path: Path) -> BackgroundRemovalResult:
        masked_path.parent.mkdir(parents=True, exist_ok=True)
        mask_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from rembg import remove

            with Image.open(original_path) as image:
                # Resize large images to max 1200px for speed (rembg is O(n²))
                w, h = image.size
                max_dim = max(w, h)
                if max_dim > 1200:
                    ratio = 1200 / max_dim
                    image = image.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                input_bytes = image.tobytes()
                # We need to pass the image object, not bytes
                output = remove(image)
                output.save(masked_path, format="PNG")
        except Exception:
            self._fallback_cutout(original_path, masked_path)

        self._write_alpha_mask(masked_path, mask_path)
        return BackgroundRemovalResult(original_path=original_path, masked_path=masked_path, mask_path=mask_path)

    def _fallback_cutout(self, original_path: Path, masked_path: Path) -> None:
        with Image.open(original_path) as image:
            image.convert("RGBA").save(masked_path, format="PNG")

    def _write_alpha_mask(self, masked_path: Path, mask_path: Path) -> None:
        with Image.open(masked_path) as image:
            alpha = image.convert("RGBA").getchannel("A")
            alpha.save(mask_path, format="PNG")
