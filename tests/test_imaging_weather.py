import io

import pytest
from PIL import Image, ImageDraw

from core.imaging import ImageError, crack_enhancement, hivis_coverage, image_metrics, prepare_image
from core.rendering import build_render_prompt, pollinations_url
from core.weather import PROTOCOLS, WEATHER_CONDITIONS, classify_conditions, daily_protocol_markdown


def _png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_prepare_image_downscales_and_converts():
    big = Image.new("RGBA", (4000, 2000), (200, 200, 200, 255))
    prepared = prepare_image(_png(big))
    assert max(prepared.image.size) == 1600
    assert prepared.image.mode == "RGB"
    assert prepared.original_size == (4000, 2000)
    assert prepared.jpeg_bytes[:2] == b"\xff\xd8"


def test_prepare_image_rejects_garbage():
    with pytest.raises(ImageError):
        prepare_image(b"definitely not an image")
    with pytest.raises(ImageError):
        prepare_image(b"")


def test_hivis_detection():
    vest = Image.new("RGB", (100, 100), (210, 255, 0))  # fluorescent yellow-green
    concrete = Image.new("RGB", (100, 100), (128, 128, 128))
    assert hivis_coverage(vest) > 0.95
    assert hivis_coverage(concrete) == 0


def test_crack_enhancement_finds_dark_line():
    surface = Image.new("RGB", (300, 300), (170, 170, 165))
    ImageDraw.Draw(surface).line([(20, 20), (280, 280)], fill=(40, 40, 40), width=3)
    overlay, coverage = crack_enhancement(surface)
    assert overlay.size == surface.size
    assert 0.005 < coverage < 0.1
    _, blank_coverage = crack_enhancement(Image.new("RGB", (300, 300), (170, 170, 165)))
    assert blank_coverage == 0


def test_image_metrics_keys():
    metrics = image_metrics(Image.new("RGB", (64, 64), (128, 128, 128)))
    assert set(metrics) == {"brightness", "contrast", "sharpness", "hivis_coverage_pct"}


@pytest.mark.parametrize(
    "reading,expected",
    [
        ((30, 32, 0, 10, 15, 1), "Normal"),
        ((30, 32, 6, 10, 15, 61), "Heavy Rain"),
        ((30, 32, 0, 10, 15, 95), "Heavy Rain"),
        ((30, 32, 0, 45, 60, 3), "High Wind"),
        ((43, 47, 0, 10, 15, 0), "Extreme Heat"),
        ((43, 47, 0, 50, 70, 95), "Heavy Rain"),  # most hazardous condition wins
    ],
)
def test_weather_classification(reading, expected):
    assert classify_conditions(*reading)[0] == expected


def test_protocols_complete():
    for condition in WEATHER_CONDITIONS:
        protocol = PROTOCOLS[condition]
        assert protocol["risk"] in {"Low", "Medium", "High", "Critical"}
        assert len(protocol["operations"]) == 6
        assert all(state in {"Go", "Restricted", "Suspended"} for state, _ in protocol["operations"].values())
    assert PROTOCOLS["High Wind"]["operations"]["Crane & Hoisting"][0] == "Suspended"
    markdown = daily_protocol_markdown("Heavy Rain", {"PPE audit": "64/100"})
    assert "Heavy Rain" in markdown and "- [ ]" in markdown and "64/100" in markdown


def test_render_prompt_and_url():
    prompt = build_render_prompt("Premium Villa", 3500, "Tier 1", "Tropical Modern", "Aerial three-quarter view", "Golden hour", 2)
    assert "Tropical Modern architectural style" in prompt and "3,500 sq ft" in prompt
    assert prompt.count("storey") == 1
    url = pollinations_url(prompt, seed=7)
    assert url.startswith("https://image.pollinations.ai/prompt/") and "seed=7" in url and " " not in url
