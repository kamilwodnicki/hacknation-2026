# Model OCR dołączony do repozytorium

| Plik | Model | Licencja | Źródło | SHA-256 |
|---|---|---|---|---|
| `PP-OCRv6_det_tiny.onnx` | PP-OCRv6 text detection, tiny (PaddleOCR, konwersja ONNX: RapidOCR 3.10.0) | Apache-2.0 | https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/det/PP-OCRv6_det_tiny.onnx | `f42c0fbd294d95eac1a550e131b277dac97462c8025fa4b6c3cec1b7894bd3d5` |

Model detekcji „tiny” jest ok. 3× szybszy od domyślnego „small” przy tej samej jakości
rozpoznawania (rozpoznawanie tekstu: PP-OCRv6 small, dołączony do pakietu `rapidocr`).
Plik jest w repozytorium, żeby obraz Dockera budował się i działał bez pobierania modeli
z zewnętrznych serwerów. Ustawienia: `OCR_DET_MODEL`, `OCR_DET_MODEL_PATH` (`src/config.py`).
