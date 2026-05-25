"""Prepare the user-provided CHEVEL logo for the web UI.

The source image has a checkerboard preview background. This script removes the
edge-connected checkerboard and writes a transparent PNG asset for the app.
"""

from __future__ import annotations

import base64
import io
import re
from collections import deque
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(r"C:\Users\mackson\OneDrive\Downloads\chevel.svg")
DEFAULT_OUTPUT = PROJECT_ROOT / "interfaces" / "chat" / "web" / "static" / "chevel-clean.png"


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def build_background_palette(image: Image.Image) -> list[tuple[int, int, int]]:
    width, height = image.size
    rgb = image.convert("RGB")
    samples: dict[tuple[int, int, int], int] = {}

    for x in range(width):
        for y in (0, height - 1):
            color = rgb.getpixel((x, y))
            samples[color] = samples.get(color, 0) + 1
    for y in range(height):
        for x in (0, width - 1):
            color = rgb.getpixel((x, y))
            samples[color] = samples.get(color, 0) + 1

    return [color for color, _ in sorted(samples.items(), key=lambda item: item[1], reverse=True)[:16]]


def looks_like_background(
    color: tuple[int, int, int],
    palette: list[tuple[int, int, int]],
) -> bool:
    # The checkerboard is made of very light neutral squares. Keep this narrow so
    # the silver logo highlights remain intact.
    if max(color) < 226:
        return False
    if max(color) - min(color) > 8:
        return False
    return any(color_distance(color, base) <= 10 for base in palette)


def load_source_image(source: Path) -> Image.Image:
    if source.suffix.lower() == ".svg":
        svg = source.read_text(encoding="utf-8")
        match = re.search(r"base64,([^\"']+)", svg)
        if not match:
            raise ValueError(f"No embedded base64 image found in {source}")
        return Image.open(io.BytesIO(base64.b64decode(match.group(1))))
    return Image.open(source)


def remove_checkerboard(source: Path, output: Path) -> None:
    image = load_source_image(source).convert("RGBA")
    width, height = image.size
    rgb = image.convert("RGB")
    palette = build_background_palette(image)

    transparent = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue_if_background(x: int, y: int) -> None:
        idx = y * width + x
        if transparent[idx]:
            return
        if looks_like_background(rgb.getpixel((x, y)), palette):
            transparent[idx] = 1
            queue.append((x, y))

    for x in range(width):
        enqueue_if_background(x, 0)
        enqueue_if_background(x, height - 1)
    for y in range(height):
        enqueue_if_background(0, y)
        enqueue_if_background(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                enqueue_if_background(nx, ny)

    pixels = image.load()
    for y in range(height):
        for x in range(width):
            idx = y * width + x
            if transparent[idx]:
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)

    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)

    # Add a little transparent padding so the mark breathes in the Ollama-style UI.
    padded = Image.new("RGBA", (image.width + 24, image.height + 24), (0, 0, 0, 0))
    padded.alpha_composite(image, (12, 12))
    output.parent.mkdir(parents=True, exist_ok=True)
    padded.save(output)


if __name__ == "__main__":
    remove_checkerboard(DEFAULT_SOURCE, DEFAULT_OUTPUT)
    print(DEFAULT_OUTPUT)
