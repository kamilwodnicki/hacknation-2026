# Architektura PISMO

```
PDF ──► 1. Odczyt ──► 2. Klasyfikacja ──► 3. Ekstrakcja ──► 4. Walidacja ──► output/*.json (UZP)
        tekst + OCR      po treści         reguły YAML        normalizacja       meta/*.meta.json (źródła)
                         (YAML)            (+ AI z UE)        sumy kontrolne
```

Jeden wspólny potok (`src/pipeline.py`) obsługuje **CLI** (`start.bat` → `python -m src process`), **API** (FastAPI) i **GUI** (Streamlit) — każdy interfejs daje identyczny wynik.

## 1. Odczyt — `src/ingestion/`

- `pypdfium2` (Apache-2.0/BSD) czyta warstwę tekstową **każdej strony osobno**.
- Strona bez tekstu (skan) jest renderowana i przekazywana do **RapidOCR** (ONNX Runtime, CPU). Wiersze OCR są składane w kolejności czytania, kolumny oddzielane szerszym odstępem.
- Wynik: tekst stron z numerami i informacją, które strony przeszły przez OCR.

## 2. Klasyfikacja — `src/classification/`

Każdy typ dokumentu ma w swoim YAML sekcję `classification`. Wynik = liczba znalezionych słów kluczowych (pierwsze 2 strony, bez względu na wielkość liter i polskie znaki) + premia za nagłówek; frazy `exclude` w nagłówku wykluczają typ. Wygrywa najwyższy wynik powyżej progu; **remis lub zbyt niski wynik = dokument nierozpoznany → `{}`** (zgodnie z wymaganiem organizatora). Nazwa pliku nie ma znaczenia.

## 3. Ekstrakcja — `src/extraction/` + `src/llm/`

- **Reguły:** silnik przechodzi po szablonie `output` z YAML i dla każdego pola próbuje strategii (`label`, `regex`, `nth_match`, `keyword_map`, `derived`, `lookup`). Listy (np. pełnomocnicy, zamawiający) są dzielone na elementy (`section`, `matches`, `whole`). Każda wartość zapisuje swoje źródło: regułę, stronę, fragment tekstu.
- **AI (opcjonalnie):** prompt budowany automatycznie z tego samego YAML (szablon JSON, opisy pól, słowniki). Tryby:
  - `rules` — bez AI,
  - `hybrid` — AI uzupełnia luki; dla wybranych pól model ma pierwszeństwo (`prefer`) lub spór rozstrzyga arbitraż (`arbitrate`),
  - `llm` — cały JSON od modelu.
- Odpowiedzi modelu są zapisywane na dysku (`cache/llm/`) — ten sam dokument nie jest opłacany dwa razy. Gdy API nie działa, wynik pochodzi z reguł.

## 4. Walidacja — `src/validation/` + `src/llm/extractor.py`

- Normalizacja do formatu UZP: daty ISO, numery bez spacji, TED `NNNNNN-YYYY`, kwoty jako liczby.
- Sumy kontrolne NIP / REGON / PESEL / IBAN (ostrzeżenie lub odrzucenie — konfigurowalne).
- `must_match` / `reject` — odrzucanie niepewnych wartości (lepiej `null` niż błąd).
- **Wartości od AI muszą występować w treści dokumentu** (identyfikatory dokładnie, nazwy po rdzeniach słów) — wymyślone dane są odrzucane. Dla imion i nazwisk AI może zmienić tylko formę odmienioną (np. „Leszkowi Wieczorkowi” → „Leszek Wieczorek”), nie płeć ani pisownię.

## Pliki wynikowe

- `output/<ta sama ścieżka>/<ta sama nazwa>.json` — wyłącznie JSON w formacie UZP.
- `meta/<…>.meta.json` — klasyfikacja (wynik każdego typu, znalezione słowa), źródło każdej wartości (reguła/AI, strona, fragment, ostrzeżenia), użycie AI (tokeny, pamięć podręczna).

## Bezpieczeństwo i koszty

- Klucz API wyłącznie w `.env` / `secrets/` (ignorowane przez git i Docker); kontener testowy ma AI wyłączone na sztywno.
- Do modelu trafia tekst dokumentu, przetwarzany przez dostawcę w UE (Mistral AI, endpoint `api.eu.mistral.ai`).
- Ewaluacja domyślnie działa bez AI; `--estimate` szacuje koszt bez wywołań API.

## Ewaluacja — `src/evaluation/`

F1 na poziomie pól zgodnie z zasadami organizatora: `null` nie jest liczony, błędna wartość = FP + FN, pola „długi string” (nazwy, tytuły) zaliczane przy podobieństwie ≥ 80%, listy dopasowywane po treści. Raporty w `reports/` (Markdown + JSON), w tym macierz pomyłek klasyfikacji i lista różnic.
