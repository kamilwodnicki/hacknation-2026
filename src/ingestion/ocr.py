"""OCR of rendered page images with RapidOCR (ONNX Runtime, CPU)."""

import threading
from dataclasses import dataclass
from statistics import mean, median

import numpy as np

_engine = None
_engine_lock = threading.Lock()


def _get_engine():
    """Create the RapidOCR engine once (model loading takes a few seconds)."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                from rapidocr import RapidOCR

                _engine = RapidOCR()
    return _engine


@dataclass(frozen=True)
class OcrBox:
    text: str
    score: float
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def y_center(self) -> float:
        return (self.y_min + self.y_max) / 2

    @property
    def height(self) -> float:
        return self.y_max - self.y_min


def group_into_lines(boxes: list[OcrBox]) -> str:
    """Rebuild reading order: boxes on the same visual line are joined left to right.

    Large horizontal gaps (columns, e.g. "Płatnik ... Rachunek obciążany") are kept as
    a wider separator so label/value pairs stay distinguishable for later steps.
    """
    if not boxes:
        return ""
    typical_height = median(b.height for b in boxes) or 1.0
    lines: list[list[OcrBox]] = []
    for box in sorted(boxes, key=lambda b: b.y_center):
        if lines and abs(box.y_center - mean(b.y_center for b in lines[-1])) <= typical_height * 0.5:
            lines[-1].append(box)
        else:
            lines.append([box])

    rendered = []
    for line in lines:
        line.sort(key=lambda b: b.x_min)
        out = line[0].text
        for prev, cur in zip(line, line[1:]):
            gap = cur.x_min - prev.x_max
            out += ("    " if gap > typical_height * 2 else " ") + cur.text
        rendered.append(out)
    return "\n".join(rendered)


def ocr_image(image_bgr: np.ndarray) -> tuple[str, float | None]:
    """Return (text, mean confidence) for one page image in BGR channel order."""
    result = _get_engine()(image_bgr)
    if not result.txts:
        return "", None
    boxes = []
    for points, text, score in zip(result.boxes, result.txts, result.scores):
        xs = [float(p[0]) for p in points]
        ys = [float(p[1]) for p in points]
        boxes.append(OcrBox(text, float(score), min(xs), max(xs), min(ys), max(ys)))
    return group_into_lines(boxes), round(mean(b.score for b in boxes), 4)
