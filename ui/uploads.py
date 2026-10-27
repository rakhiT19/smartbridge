"""Cached image ingestion shared by the vision tabs (Pillow work runs once per image)."""
from __future__ import annotations

from typing import Dict, Optional, Tuple

import streamlit as st

from core.imaging import ImageError, PreparedImage, crack_enhancement, image_metrics, prepare_image, to_png_bytes


@st.cache_data(show_spinner=False, max_entries=8)
def _prepare(data: bytes) -> PreparedImage:
    return prepare_image(data)


@st.cache_data(show_spinner=False, max_entries=8)
def metrics_for(digest: str, _image: PreparedImage) -> Dict[str, float]:
    return image_metrics(_image.image)


@st.cache_data(show_spinner=False, max_entries=8)
def crack_map_for(digest: str, _image: PreparedImage) -> Tuple[bytes, float]:
    overlay, coverage = crack_enhancement(_image.image)
    return to_png_bytes(overlay), coverage


def load_upload(upload) -> Optional[PreparedImage]:
    """Return a prepared image, or None (with an inline error) if the upload is unusable."""
    if upload is None:
        return None
    try:
        return _prepare(upload.getvalue())
    except ImageError as exc:
        st.error(str(exc), icon="🖼️")
        return None
