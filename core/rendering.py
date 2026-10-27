"""Conceptual 3D architectural rendering via the Pollinations (Flux) image API."""
from __future__ import annotations

from urllib.parse import quote, urlencode

import requests

from core.config import POLLINATIONS_ENDPOINT, STRUCTURE_TYPES

TIER_CONTEXT = {
    "Tier 1": "dense metropolitan Indian skyline context",
    "Tier 2": "growing Indian city neighbourhood with tree-lined streets",
    "Tier 3": "calm semi-urban Indian town setting with greenery",
}


class RenderError(Exception):
    """Raised when the rendering service fails or returns a non-image."""


def build_render_prompt(structure_type: str, built_up_sqft: float, tier: str, style: str,
                        view: str, time_of_day: str, floors: int) -> str:
    subject = STRUCTURE_TYPES[structure_type]["render_subject"]
    storeys = "single-storey" if floors == 1 else f"{floors}-storey"
    return (
        f"Photorealistic architectural visualization of a {storeys} {subject} in {style} architectural style, "
        f"approximately {int(built_up_sqft):,} sq ft built-up area, in a {TIER_CONTEXT[tier]}. "
        f"{view}, {time_of_day.lower()} lighting, exposed concrete, glass and natural stone, "
        "landscaped surroundings, people for scale, ultra-detailed 3D render, V-Ray, 8k, architectural digest quality"
    )


def pollinations_url(prompt: str, width: int = 1024, height: int = 640, seed: int = 42, model: str = "flux") -> str:
    query = urlencode({"width": width, "height": height, "seed": seed, "model": model, "nologo": "true"})
    return f"{POLLINATIONS_ENDPOINT}{quote(prompt, safe='')}?{query}"


def _service_message(response: requests.Response) -> str:
    try:
        return str(response.json()["error"]["message"])[:220]
    except (ValueError, KeyError, TypeError):
        return ""


def fetch_render(url: str, timeout: int = 120) -> bytes:
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise RenderError(f"Rendering service unavailable ({exc.__class__.__name__}).") from exc
    if response.status_code in (402, 429):
        detail = _service_message(response) or "Free-tier rate limit reached."
        raise RenderError(f"Pollinations rate limit: {detail} Wait about a minute and try again.")
    if not response.ok:
        raise RenderError(f"Rendering service returned HTTP {response.status_code}.")
    if not response.headers.get("content-type", "").startswith("image/"):
        raise RenderError("Rendering service returned an unexpected response.")
    return response.content
