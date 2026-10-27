"""Google Gemini multimodal client with robust JSON extraction and friendly errors."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from core.config import LLM_TIMEOUT_SECONDS


class LLMError(Exception):
    """Raised with a user-facing message when a model call fails."""


def extract_json(text: Optional[str]) -> Dict[str, Any]:
    """Parse a JSON object from model output, tolerating code fences and stray prose."""
    if not text or not text.strip():
        raise LLMError("The model returned an empty response.")
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise LLMError("The model response did not contain a JSON object.")
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Could not parse the model's JSON ({exc.msg}).") from exc
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if not isinstance(data, dict):
        raise LLMError("The model's JSON was not an object.")
    return data


def friendly_error(exc: Exception) -> str:
    """Translate SDK / transport exceptions into actionable messages."""
    message = str(exc)
    lowered = message.lower()
    code = getattr(exc, "code", None)
    if "api_key_invalid" in lowered or "api key not valid" in lowered or code in (401, 403):
        return "Gemini rejected the API key. Check the key in the sidebar or remove it to use demonstration mode."
    if code == 429 or "resource_exhausted" in lowered or "quota" in lowered:
        return "Gemini rate limit or quota reached. Wait a minute, or switch to a lighter model in the sidebar."
    if code == 404 or ("model" in lowered and "not found" in lowered):
        return "The selected model is not available for this key. Choose another model in the sidebar."
    if isinstance(code, int) and code >= 500:
        return "The Gemini service is temporarily unavailable. Please retry shortly."
    if "timed out" in lowered or "timeout" in lowered:
        return "The request to Gemini timed out. Try again or use a smaller image."
    if "connect" in lowered or "network" in lowered or "resolve" in lowered:
        return "Could not reach the Gemini API. Check your internet connection."
    return f"Gemini request failed: {message[:280]}"


class GeminiClient:
    """Thin wrapper over the `google-genai` SDK used by every AI feature."""

    def __init__(self, api_key: str, model: str, timeout_seconds: int = LLM_TIMEOUT_SECONDS):
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise LLMError("The google-genai package is missing. Run: pip install -r requirements.txt") from exc
        self._types = types
        self.model = model
        try:
            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=timeout_seconds * 1000),
            )
        except Exception as exc:
            raise LLMError(friendly_error(exc)) from exc

    def _generate(self, contents: Any, system: Optional[str], json_mode: bool, temperature: float) -> str:
        config = self._types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        try:
            response = self._client.models.generate_content(model=self.model, contents=contents, config=config)
        except Exception as exc:
            raise LLMError(friendly_error(exc)) from exc
        try:
            text = response.text
        except Exception:  # some SDK versions raise when no text part exists
            text = None
        if not text:
            feedback = getattr(response, "prompt_feedback", None)
            reason = getattr(feedback, "block_reason", None)
            if reason:
                raise LLMError(f"The request was blocked by Gemini safety filters ({reason}). Try a different image.")
            raise LLMError("Gemini returned no content. Please try again.")
        return text

    def analyze_image(self, prompt: str, image_bytes: bytes, mime_type: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Send an image + instruction and return the parsed JSON object."""
        parts = [self._types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt]
        return extract_json(self._generate(parts, system, json_mode=True, temperature=0.2))

    def generate_text(self, prompt: str, system: Optional[str] = None, temperature: float = 0.6) -> str:
        return self._generate(prompt, system, json_mode=False, temperature=temperature).strip()

    def chat(self, history: List[Dict[str, str]], system: str) -> str:
        """Stateless multi-turn chat: the full history is replayed on each call."""
        contents = [
            self._types.Content(
                role="user" if turn["role"] == "user" else "model",
                parts=[self._types.Part.from_text(text=turn["content"])],
            )
            for turn in history
            if turn.get("content")
        ]
        return self._generate(contents, system, json_mode=False, temperature=0.5).strip()
