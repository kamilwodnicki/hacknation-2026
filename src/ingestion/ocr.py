"""OCR of rendered page images with RapidOCR (ONNX Runtime, CPU)."""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import numpy as np

log = logging.getLogger(__name__)
_engines: dict[tuple, object] = {}
_engine_lock = threading.Lock()
_run_lock = threading.Lock()
"""OCR uses all CPU cores already: one page at a time, also when documents run in parallel."""


def engine_params(
    det_model: str = "tiny", det_model_path: Path | None = None, use_cls: bool = False, engine: str = "onnxruntime"
) -> dict:
    from rapidocr import EngineType, ModelType

    params: dict = {"Global.use_cls": use_cls, "Global.log_level": "warning"}
    if engine == "openvino":
        for stage in ("Det", "Cls", "Rec"):
            params[f"{stage}.engine_type"] = EngineType.OPENVINO
    if det_model == "tiny":
        params["Det.model_type"] = ModelType.TINY
        if det_model_path and Path(det_model_path).is_file():
            params["Det.model_path"] = str(det_model_path)
    return params


def _get_engine(det_model: str, det_model_path: Path | None, use_cls: bool, engine: str = "onnxruntime"):
    """Create each RapidOCR engine once (model loading takes a few seconds)."""
    key = (det_model, str(det_model_path), use_cls, engine)
    if key not in _engines:
        with _engine_lock:
            if key not in _engines:
                from rapidocr import RapidOCR

                try:
                    _engines[key] = RapidOCR(params=engine_params(det_model, det_model_path, use_cls, engine))
                except Exception as exc:
                    if engine == "onnxruntime":
                        raise
                    log.warning("OCR: silnik %s niedostępny (%s) — używam onnxruntime", engine, exc)
                    _engines[key] = RapidOCR(params=engine_params(det_model, det_model_path, use_cls))
                # RapidOCR logs every model load at INFO level; keep the console readable.
                logging.getLogger("RapidOCR").setLevel(logging.WARNING)
    return _engines[key]


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


def ocr_image(
    image_bgr: np.ndarray,
    det_model: str = "tiny",
    det_model_path: Path | None = None,
    use_cls: bool = False,
    engine_type: str = "onnxruntime",
) -> tuple[str, float | None]:
    """Return (text, mean confidence) for one page image in BGR channel order."""
    engine = _get_engine(det_model, det_model_path, use_cls, engine_type)
    with _run_lock:
        result = engine(image_bgr)
    if not result.txts:
        return "", None
    boxes = []
    for points, text, score in zip(result.boxes, result.txts, result.scores):
        xs = [float(p[0]) for p in points]
        ys = [float(p[1]) for p in points]
        boxes.append(OcrBox(text, float(score), min(xs), max(xs), min(ys), max(ys)))
    return group_into_lines(boxes), round(mean(b.score for b in boxes), 4)
