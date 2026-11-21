# PISMO — Parser Inteligentnie Strukturyzujący Materiały Odwoławcze

**Od PDF-a sprawy KIO do danych JSON.** Rozwiązanie wyzwania *Odwołania2json* (HackNation 2026, Urząd Zamówień Publicznych).

PISMO przyjmuje dokumenty sprawy odwoławczej (odwołanie, pełnomocnictwo, potwierdzenie przelewu — PDF cyfrowe lub skany), **rozpoznaje typ dokumentu po treści**, wyodrębnia dane i zapisuje JSON **ściśle zgodny z modelem UZP** (`oczekiwane-json`). Dokument spoza obsługiwanych klas daje plik z `{}`.

![PISMO](docs/grafika_pismo.png)

- **Działa lokalnie w Dockerze**, na zwykłym laptopie bez GPU (OCR na CPU).
- **Konfiguracja zamiast kodu:** typy dokumentów, pola, reguły i rozpoznawanie — w plikach YAML.
- **Trzy tryby:** same reguły (bez AI, bez kosztów), reguły + AI (hybryda) albo samo AI — otwarty model hostowany w UE.
- **Przejrzystość:** przy każdej wartości wiadomo, z której strony i z jakiego fragmentu pochodzi oraz czy dała ją reguła, czy AI.

---

## Szybki start (CLI) — przetwarzanie folderu `input/`

**Wymagania:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / macOS) albo Docker + Docker Compose (Linux). Nic więcej nie trzeba instalować.

1. Umieść sprawy w folderze `input/` (dowolne podfoldery, dowolne nazwy plików):
   ```
   input/
   ├── case1/
   │   ├── odwolanie_nr_1.pdf
   │   ├── pelnomocnictwo_nr_1.pdf
   │   └── przelew_nr_1.pdf
   └── case2/ ...
   ```
2. Uruchom:
   - **Windows:** dwuklik na `start.bat` albo w terminalu `.\start.bat`
     (w `cmd` wpisz `.\start.bat` — samo `start.bat` cmd myli z wbudowanym poleceniem `START`)
   - **Linux / macOS:** `sh start.sh`
3. Wyniki pojawią się w `output/` — **ta sama struktura folderów i te same nazwy plików**, z rozszerzeniem `.json`:
   ```
   output/
   ├── case1/
   │   ├── odwolanie_nr_1.json
   │   ├── pelnomocnictwo_nr_1.json
   │   └── przelew_nr_1.json
   ```
   Metadane ekstrakcji (klasyfikacja, źródło każdej wartości) trafiają osobno do `meta/`, żeby `output/` zawierał wyłącznie JSON-y w formacie UZP.

Przy pierwszym uruchomieniu Docker buduje obraz (kilka minut); kolejne uruchomienia startują od razu.

Bez Dockera (Python 3.13+): `pip install -r requirements.txt`, potem `python -m src process --input input --output output`.

## Ustawienia i tryb z AI (klucz API)

**Domyślnie aplikacja korzysta z AI** (tryb `hybrid`, Mistral AI — endpoint UE). Potrzebny jest tylko klucz API; bez klucza aplikacja działa na samych regułach i informuje o tym.

Ustawienia są czytane z **jednego** pliku w głównym folderze projektu:

| Plik | Kiedy jest używany |
|---|---|
| `.env.overdrive` | **jeśli istnieje — ma pierwszeństwo, a `.env` jest całkowicie pomijany** |
| `.env` | gdy nie ma `.env.overdrive` (tworzony z `.env.example` przy pierwszym uruchomieniu `start.bat` / `start.sh`) |

Oba pliki są w `.gitignore` — klucz nigdy nie trafia do repozytorium.

**Dla jury:** plik `.env.overdrive` z kluczem przekazujemy osobno, poza publicznym repozytorium — wystarczy umieścić go w głównym folderze projektu i uruchomić `start.bat` / `start.sh`.

Własna konfiguracja (w `.env` lub `.env.overdrive`):
```
LLM_API_KEY=<klucz z https://console.mistral.ai>
EXTRACTION_MODE=hybrid        # rules | hybrid | llm
```

| `EXTRACTION_MODE` | Działanie |
|---|---|
| `rules` | tylko reguły z YAML (bez AI, bez kosztów) |
| `hybrid` (zalecany) | najpierw reguły, potem AI uzupełnia luki i rozstrzyga trudne pola (powód odwołania, data czynności, imiona i nazwiska w mianowniku); spory reguła–AI rozstrzyga krótkie drugie zapytanie (arbitraż) |
| `llm` | cały JSON od modelu (reguły nieużywane) |

Jeśli API jest niedostępne, aplikacja nie przerywa pracy — zwraca wynik z reguł i zapisuje informację w metadanych.

### Użyty model językowy

| | |
|---|---|
| Model | **Ministral 3 14B** (`ministral-14b-2512`) — otwarte wagi, licencja **Apache 2.0**, możliwy do instalacji lokalnej |
| Dostawca | **Mistral AI** (Francja), endpoint UE: `https://api.eu.mistral.ai/v1` |
| Przetwarzanie danych | centra danych w UE (endpoint regionalny UE) — [polityka prywatności i kontrola danych Mistral AI](https://docs.mistral.ai/admin/security-access/privacy) |
| Koszt | ok. $0,20 / 1 mln tokenów; **ok. 10 gr za 100 stron** w trybie z AI |
| Zapasowo | Google Cloud Vertex AI, Mistral Small 3.1 w regionie `europe-west4` (`LLM_PROVIDER=vertex`) |

Do modelu wysyłany jest tekst dokumentu. Każda odpowiedź AI przechodzi te same kontrole co reguły (format, sumy kontrolne NIP/REGON/PESEL/IBAN) **i musi występować w treści dokumentu** — wartości wymyślone przez model są odrzucane. Odpowiedzi są zapisywane w `cache/llm/`, więc ten sam dokument nie jest opłacany dwa razy.

## GUI i API

```
docker compose up -d --build
```

- **GUI:** http://localhost:8501 — wgranie PDF-ów, uruchomienie analizy, **podgląd strony dokumentu obok wyodrębnionych danych**; wybór pola pokazuje stronę i fragment, z którego pochodzi wartość. Pobieranie JSON-ów (pojedynczo lub ZIP).
- **API:** http://localhost:8000/docs
  - `POST /extract` — wgrany PDF → JSON (UZP) + metadane (klasyfikacja, źródło pól, użycie AI)
  - `GET /document-types` — typy dokumentów wczytane z konfiguracji
  - `GET /health`

## Jakość — wyniki testów

Ewaluacja na zbiorze treningowym organizatora (60 spraw × 3 dokumenty + 17 dokumentów negatywnych), metodą zgodną z zasadami UZP: F1 na poziomie pól, pola typu „długi string” zaliczane przy podobieństwie ≥ 80%, listy dopasowywane po treści.

| | Tylko reguły | Hybryda (reguły + AI) |
|---|---|---|
| **F1 łącznie** | **0,998** | **1,000** |
| odwołanie | 0,996 | 1,000 |
| pełnomocnictwo | 1,000 | 1,000 |
| potwierdzenie przelewu | 1,000 | 1,000 |
| klasyfikacja (198 dokumentów, w tym 17 negatywnych) | 198/198 | 198/198 |

Pełne raporty: [`reports/uzp_training.md`](reports/uzp_training.md) (reguły), [`reports/uzp_training_hybrid.md`](reports/uzp_training_hybrid.md) (hybryda). **Uwaga:** to wyniki na danych, na których budowaliśmy reguły — na nowych dokumentach należy spodziewać się niższych wartości; tryb hybrydowy jest na to lepiej przygotowany (AI uzupełnia pola, których reguły nie znajdą).

Uruchomienie ewaluacji (dane organizatora wskazane w `.env` jako `UZP_DATA_DIR`):
```
docker compose run --rm tests python -m src.evaluation                     # tylko reguły (bezpłatnie)
docker compose run --rm -e LLM_PROVIDER=openai tests python -m src.evaluation --mode hybrid --estimate   # szacunek kosztu
docker compose run --rm -e LLM_PROVIDER=openai tests python -m src.evaluation --mode hybrid
docker compose run --rm tests                                              # testy automatyczne (bez płatnych wywołań)
```

## Dodawanie nowego typu dokumentu (bez programowania)

Nowy typ dokumentu to **jeden plik YAML** w `config/document_types/` — po zapisaniu jest od razu rozpoznawany i przetwarzany (CLI, API, GUI, tryb z AI). Instrukcja krok po kroku: [`docs/nowy-typ-dokumentu.md`](docs/nowy-typ-dokumentu.md). Architektura: [`docs/architektura.md`](docs/architektura.md).

## Znane ograniczenia

- **Imiona i nazwiska w trybie samych reguł** są zwracane w formie z dokumentu. Automatyczna odmiana polskich nazwisk regułami nie może być w 100% poprawna (np. „Leszkowi → Leszek”, ale „Kowalikowi → Kowalik”; nieodmienne nazwiska żeńskie), dlatego mianownik zapewnia tryb z AI.
- **OCR skanów** działa na CPU — ok. 7–8 s na stronę.
- **Wyniki 1,000 / 0,998** dotyczą zbioru treningowego (patrz wyżej).

## Struktura projektu

```
config/document_types/   typy dokumentów (YAML): klasyfikacja, pola, reguły, zasady AI
config/dictionaries/     słowniki (np. powody odwołania 1–12)
config/evaluation/       zbiory ewaluacyjne i zasady metryki
src/ingestion/           PDF → tekst (pypdfium2) + OCR skanów (RapidOCR / ONNX, CPU)
src/classification/      rozpoznawanie typu dokumentu po treści
src/extraction/          silnik reguł sterowany YAML
src/validation/          typy wartości, normalizacja, sumy kontrolne
src/llm/                 klienci LLM, prompt ze schematu YAML, walidacja i scalanie, pamięć odpowiedzi
src/evaluation/          metryka F1 zgodna z UZP, raporty
src/cli.py, src/api/     CLI (input/ → output/) i API (FastAPI)
ui/app.py                GUI (Streamlit)
tests/                   testy automatyczne (AI zastąpione atrapą — bez kosztów)
```

Wszystkie komponenty są open source (MIT / BSD / Apache-2.0); wersje bibliotek przypięte w `requirements.txt`.
