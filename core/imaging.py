"""Pillow pre-processing: safe loading, downscaling and lightweight image forensics."""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from typing import Dict, Tuple

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

from core.config import MAX_IMAGE_SIDE, MAX_UPLOAD_MB


class ImageError(Exception):
    """Raised with a user-facing message when an upload cannot be processed."""


@dataclass
class PreparedImage:
    image: Image.Image  # RGB, downscaled
    jpeg_bytes: bytes  # payload sent to the multimodal model
    digest: str  # content hash used to cache analyses per image
    original_size: Tuple[int, int]

    @property
    def mime_type(self) -> str:
        return "image/jpeg"


def prepare_image(data: bytes, max_side: int = MAX_IMAGE_SIDE) -> PreparedImage:
    """Validate, orient, convert to RGB and downscale an uploaded image."""
    if not data:
        raise ImageError("The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ImageError(f"Image exceeds the {MAX_UPLOAD_MB} MB limit.")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image)
        original_size = image.size
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        else:
            image = image.convert("RGB")
        image.thumbnail((max_side, max_side), Image.LANCZOS)
    except (UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ImageError("This file is not a readable JPG/PNG image.") from exc
    except (OSError, ValueError, SyntaxError) as exc:
        raise ImageError(f"The image appears to be corrupted ({exc}).") from exc

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90, optimize=True)
    return PreparedImage(
        image=image,
        jpeg_bytes=buffer.getvalue(),
        digest=hashlib.sha256(data).hexdigest()[:16],
        original_size=original_size,
    )


def _ratio(mask: Image.Image) -> float:
    histogram = mask.histogram()
    total = mask.size[0] * mask.size[1]
    return histogram[255] / total if total else 0.0


def hivis_coverage(image: Image.Image) -> float:
    """Fraction of pixels in the fluorescent yellow-green / orange band of hi-vis garments."""
    hue, sat, val = image.convert("HSV").split()
    hue_mask = hue.point(lambda h: 255 if 10 <= h <= 57 else 0)  # ≈14°–80° on the colour wheel
    sat_mask = sat.point(lambda s: 255 if s >= 150 else 0)
    val_mask = val.point(lambda v: 255 if v >= 140 else 0)
    return _ratio(ImageChops.multiply(ImageChops.multiply(hue_mask, sat_mask), val_mask))


def image_metrics(image: Image.Image) -> Dict[str, float]:
    """Exposure and sharpness indicators used to flag low-quality evidence photos."""
    gray = ImageOps.grayscale(image)
    stat = ImageStat.Stat(gray)
    edges = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES))
    return {
        "brightness": round(stat.mean[0] / 255 * 100, 1),
        "contrast": round(stat.stddev[0] / 128 * 100, 1),
        "sharpness": round(edges.stddev[0], 1),
        "hivis_coverage_pct": round(hivis_coverage(image) * 100, 2),
    }


def quality_warnings(metrics: Dict[str, float]) -> list:
    warnings = []
    if metrics["brightness"] < 22:
        warnings.append("Image is very dark — detections may be unreliable.")
    elif metrics["brightness"] > 88:
        warnings.append("Image is over-exposed — fine details may be lost.")
    if metrics["contrast"] < 18:
        warnings.append("Low contrast — consider a photo with better lighting.")
    if metrics["sharpness"] < 8:
        warnings.append("Image looks blurred — hold the camera steady or move closer.")
    return warnings


def crack_enhancement(image: Image.Image, threshold: int = 28) -> Tuple[Image.Image, float]:
    """Highlight thin dark features (crack candidates) against the local background.

    Each pixel is compared with a blurred local mean; pixels notably darker than their
    surroundings are kept, de-speckled, and painted red over a dimmed copy of the photo.
    Returns the overlay and the fraction of the surface flagged as crack-like.
    """
    gray = ImageOps.autocontrast(ImageOps.grayscale(image), cutoff=1)
    background = gray.filter(ImageFilter.BoxBlur(12))
    darker = ImageChops.subtract(background, gray)
    mask = darker.point(lambda v: 255 if v > threshold else 0).filter(ImageFilter.MedianFilter(3))
    coverage = _ratio(mask)

    display_mask = mask.filter(ImageFilter.MaxFilter(3))
    dimmed = ImageOps.grayscale(image).convert("RGB").point(lambda v: int(v * 0.55 + 40))
    highlight = Image.new("RGB", image.size, (230, 57, 70))
    return Image.composite(highlight, dimmed, display_mask), coverage


def to_png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
