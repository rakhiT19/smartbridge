"""Orchestrates image analyses: live Gemini call → JSON contract, with demo fallbacks."""
from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

from core.imaging import PreparedImage
from core.llm import LLMError
from core.settings import AppSettings

Normalizer = Callable[..., Dict[str, Any]]


def run_image_analysis(
    settings: AppSettings,
    image: Optional[PreparedImage],
    prompt: str,
    system: str,
    normalizer: Normalizer,
    sample: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return a contract-valid report.

    * No API key (or no image in demo mode) → the labelled sample report.
    * Live call fails for any reason → the sample report flagged as a fallback,
      carrying the user-facing error so the UI can explain what happened.
    """
    if not settings.live or image is None:
        return normalizer(sample, source="demo")
    try:
        raw = settings.client().analyze_image(prompt, image.jpeg_bytes, image.mime_type, system)
        return normalizer(raw, source="live", model=settings.model)
    except LLMError as exc:
        report = normalizer(sample, source="fallback")
        report["error"] = str(exc)
        return report
